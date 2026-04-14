import os
import json
import ezdxf
import trimesh
import cadquery as cq
import numpy as np
from datetime import datetime
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_EDGE
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GeomAbs import GeomAbs_Line, GeomAbs_Circle, GeomAbs_Ellipse
from OCP.TopoDS import TopoDS

def get_coord(p, axis):
    """Safe retrieval of coordinate components from gp_Pnt."""
    return [p.X(), p.Y(), p.Z()][axis]

class ProDraftingEngine:
    """Industrial Drafting Engine using OpenCASCADE HLR."""
    
    def __init__(self, specs, model_size):
        self.specs = specs
        self.doc = ezdxf.new()
        self.msp = self.doc.modelspace()
        self.model_size = model_size
        
        # Scaling Linetypes
        dash = model_size * 0.05
        gap = dash / 2
        self.doc.linetypes.new("DASHED", dxfattribs={
            "description": "Dashed", 
            "pattern": [dash, -gap]
        })
        
        # Define Layers
        self.doc.layers.new("VISIBLE", dxfattribs={"color": 7})
        self.doc.layers.new("HIDDEN", dxfattribs={"color": 8, "linetype": "DASHED"})
        
        # Adaptive Threshold
        self.threshold = max(0.5, model_size * 0.001)

    def _draw_compound(self, compound, offset, layer, axes=(0, 1)):
        """Extracts and draws edges from an OCP Compound."""
        if not compound:
            return
            
        explorer = TopExp_Explorer(compound, TopAbs_EDGE)
        offset_x, offset_y = offset
        
        while explorer.More():
            edge = TopoDS.Edge_s(explorer.Current())
            adaptor = BRepAdaptor_Curve(edge)
            curve_type = adaptor.GetType()
            
            p1 = adaptor.Value(adaptor.FirstParameter())
            p2 = adaptor.Value(adaptor.LastParameter())
            
            # Adaptive Filtering
            if p1.Distance(p2) < self.threshold:
                explorer.Next()
                continue
            
            coords = lambda p: (get_coord(p, axes[0]) + offset_x, get_coord(p, axes[1]) + offset_y)
            
            if curve_type == GeomAbs_Line:
                self.msp.add_line(coords(p1), coords(p2), dxfattribs={"layer": layer})
            
            elif curve_type == GeomAbs_Circle:
                circle = adaptor.Circle()
                center = circle.Location()
                radius = circle.Radius()
                self.msp.add_circle(coords(center), radius, dxfattribs={"layer": layer})
                                    
            elif curve_type == GeomAbs_Ellipse:
                el = adaptor.Ellipse()
                center = el.Location()
                major_dir = el.XAxis().Direction()
                # Construct major axis vector in 2D space based on view mapping
                major_vec = (major_dir.XYZ().GetData()[axes[0]] * el.MajorRadius(),
                           major_dir.XYZ().GetData()[axes[1]] * el.MajorRadius())
                ratio = el.MinorRadius() / el.MajorRadius()
                self.msp.add_ellipse(coords(center), major_vec, ratio, dxfattribs={"layer": layer})
                                     
            explorer.Next()

    def generate_views(self, solid_wrapped, spacing_factor=1.6):
        """Generates aligned orthographic views."""
        spacing = self.model_size * spacing_factor
        
        views = [
            {"name": "FRONT VIEW", "dir": (0, -1, 0), "up": (0, 0, 1), "offset": (0, 0), "axes": (0, 2)},
            {"name": "SIDE VIEW",  "dir": (-1, 0, 0), "up": (0, 0, 1), "offset": (spacing, 0), "axes": (1, 2)},
            {"name": "TOP VIEW",   "dir": (0, 0, -1), "up": (0, 1, 0), "offset": (0, spacing), "axes": (0, 1)}
        ]
        
        for view in views:
            ax2 = gp_Ax2(gp_Pnt(0,0,0), gp_Dir(*view["dir"]), gp_Dir(*view["up"]))
            
            hlr = HLRBRep_Algo()
            hlr.Add(solid_wrapped)
            hlr.Projector(HLRAlgo_Projector(ax2))
            hlr.Update()
            hlr.Hide()
            
            hlr_shape = HLRBRep_HLRToShape(hlr)
            v_comp = hlr_shape.VCompound()
            h_comp = hlr_shape.HCompound()
            
            if not v_comp:
                print(f"[Agent 2] !! Warning: Empty projection for {view['name']}")
                
            self._draw_compound(v_comp, view["offset"], "VISIBLE", axes=view["axes"])
            self._draw_compound(h_comp, view["offset"], "HIDDEN", axes=view["axes"])
            self.msp.add_text(view["name"], dxfattribs={'height': 7}).set_placement((view["offset"][0], view["offset"][1] - 25))

    def add_title_block(self):
        """Standardized industrial title block."""
        lower_x, lower_y = -100, -200
        name = self.specs.get("equipment_category", "PART").upper()
        
        info = [
            f"PART NAME: {name}",
            f"MATERIAL: {self.specs.get('material', '316L')}",
            f"DIAMETER: {self.specs.get('dimensions', {}).get('nominal_diameter_mm', 'N/A')} mm",
            f"PRESSURE: {self.specs.get('pressure', 'N/A')} bar",
            f"DATE: {datetime.now().strftime('%Y-%m-%d')}",
            f"SCALE: 1:1"
        ]
        
        pts = [(lower_x, lower_y), (lower_x + 400, lower_y), (lower_x + 400, lower_y + 120), (lower_x, lower_y + 120), (lower_x, lower_y)]
        self.msp.add_lwpolyline(pts)
        for i, text in enumerate(info):
            self.msp.add_text(text, dxfattribs={'height': 8}).set_placement((lower_x + 10, lower_y + 100 - (i * 18)))

class ProceduralCADEngine:
    def __init__(self, specs):
        self.specs = specs
        self.category = specs.get("equipment_category", "generic").lower()
        dims = specs.get("dimensions", {})
        self.diameter = dims.get("nominal_diameter_mm", 100)
        self.length = dims.get("overall_length_mm", 200)
        self.radius = self.diameter / 2
        
    def build(self):
        if self.category == "pump":
            return self._build_pump()
        elif self.category == "valve":
            return self._build_valve()
        return cq.Workplane("XY").circle(self.radius).extrude(self.length)

    def _build_pump(self):
        vol_r, vol_h = self.radius * 1.5, self.diameter * 0.8
        ecc = vol_r * 0.2
        body = cq.Workplane("XY").center(ecc, 0).circle(vol_r).extrude(vol_h)
        inlet = cq.Workplane("XY").workplane(offset=-50).circle(self.radius).extrude(55)
        out_r = self.radius * 0.8
        outlet = cq.Workplane("YZ").workplane(offset=-10).center(vol_h/2, vol_r + ecc - out_r).circle(out_r).extrude(70)
        base = cq.Workplane("XY").workplane(offset=-55).box(vol_r * 2.2, vol_r * 2.2, 15, centered=(True, True, False))
        return body.union(inlet).union(outlet).union(base)

    def _build_valve(self):
        body = cq.Workplane("XY").circle(self.radius).extrude(self.length)
        globe = cq.Workplane("XY").workplane(offset=self.length/2).sphere(self.radius*1.3)
        f = self.radius * 1.6
        f1 = cq.Workplane("XY").circle(f).extrude(15)
        f2 = cq.Workplane("XY").workplane(offset=self.length-15).circle(f).extrude(15)
        return body.union(f1).union(f2).union(globe)

def run_agent2(state):
    specs = state.get("specs")
    if not isinstance(specs, dict):
        raise ValueError("Invalid specs from Agent 1")
        
    engine = ProceduralCADEngine(specs)
    solid = engine.build()
    
    # 3D Data
    run_id = state.get("run_id")
    if not run_id:
        raise ValueError("Agent 2 requires a valid run_id in state")
        
    out = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "outputs", run_id, "agent2"))
    os.makedirs(out, exist_ok=True)
    name = specs.get("equipment_category", "part").lower().replace(" ", "_")
    
    # STEP
    step_path = os.path.join(out, f"{name}.step")
    cq.exporters.export(solid, step_path, cq.exporters.ExportTypes.STEP)
    
    # OBJ & Mesh Verification
    v, i = solid.val().tessellate(0.1)
    mesh = trimesh.Trimesh(vertices=[[pt.x, pt.y, pt.z] for pt in v], faces=i)
    obj_path = os.path.join(out, f"{name}.obj")
    mesh.export(obj_path)
    
    # PNG
    png_path = os.path.join(out, f"{name}.png")
    try:
        scene = trimesh.Scene(mesh)
        png_data = scene.save_image(resolution=(1024, 768))
        with open(png_path, "wb") as f: f.write(png_data)
    except: png_path = None

    # DXF
    bbox = solid.val().BoundingBox()
    model_size = max(bbox.xlen, bbox.ylen, bbox.zlen)
    dxf_path = os.path.join(out, f"{name}.dxf")
    drafting = ProDraftingEngine(specs, model_size)
    drafting.generate_views(solid.val().wrapped)
    drafting.add_title_block()
    drafting.doc.saveas(dxf_path)
    
    # State update
    state.update({
        "step": step_path, "obj": obj_path, "png": png_path, "dxf": dxf_path,
        "validation": {
            "status": "OK",
            "vertices": len(mesh.vertices),
            "faces": len(mesh.faces),
            "is_watertight": mesh.is_watertight,
            "bbox": {"x": bbox.xlen, "y": bbox.ylen, "z": bbox.zlen}
        }
    })
    print(f"[Agent 2] Engineering package complete for: {name}")
    return state
