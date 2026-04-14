import trimesh
import pyrender
import numpy as np

class SceneBuilder:
    """Builds a high-fidelity industrial 3D scene from an OBJ file."""
    
    def __init__(self, obj_path):
        self.obj_path = obj_path
        self.scene = pyrender.Scene(bg_color=[0.05, 0.05, 0.05]) # Dark industrial background
        self.mesh_node = None
        self.camera_node = None
        self.raw_mesh = None
        self.center = np.zeros(3)
        self.radius = 1.0

    def load_model(self):
        """Loads OBJ and scales/centers for optimal rendering."""
        mesh = trimesh.load(self.obj_path)
        
        # Merge if it's a scene
        if isinstance(mesh, trimesh.Scene):
            mesh = mesh.dump(concatenate=True)

        # Fix normals for industrial lighting
        mesh.fix_normals()
        
        # Calculate bounding info
        self.center = mesh.centroid
        radius_raw = mesh.bounding_sphere.primitive.radius
        
        # Normalize scale and center
        scale_factor = 1.0 / radius_raw if radius_raw > 0 else 1.0
        mesh.vertices = (mesh.vertices - self.center) * scale_factor
        
        # Update normalized metrics
        self.center = np.zeros(3)
        self.radius = 1.0
        
        # Save a copy for fallback mechanism
        self.raw_mesh = mesh.copy()
        
        # Material: Industrial Steel (PBR)
        material = pyrender.MetallicRoughnessMaterial(
            metallicFactor=1.0,
            roughnessFactor=0.4,
            baseColorFactor=[0.7, 0.7, 0.7, 1.0]
        )
        
        render_mesh = pyrender.Mesh.from_trimesh(mesh, material=material)
        self.mesh_node = self.scene.add(render_mesh)
        return mesh

    def setup_camera(self):
        """Auto-frames the camera based on the model's bounding sphere."""
        camera = pyrender.PerspectiveCamera(yfov=np.pi / 4.0, aspectRatio=1.77) # 16:9
        
        # Calculate safe distance (simple trigonometry)
        distance = self.radius * 3.5 
        
        # Initial pose (looking at origin)
        self.camera_pose = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, distance],
            [0, 0, 0, 1]
        ])
        
        self.camera_node = self.scene.add(camera, pose=self.camera_pose)
        return distance

    def setup_lighting(self):
        """Industrial 3-point lighting setup."""
        # 1. Key Light (Stronger, dynamic angle later)
        key_light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=8.0)
        self.scene.add(key_light, pose=self._look_at_origin([self.radius*2, self.radius*2, self.radius*2]))
        
        # 2. Fill Light (Softer, opposite side)
        fill_light = pyrender.DirectionalLight(color=[0.8, 0.9, 1.0], intensity=3.0)
        self.scene.add(fill_light, pose=self._look_at_origin([-self.radius*2, -self.radius, self.radius]))
        
        # 3. Back Light (Rim highlighting)
        back_light = pyrender.PointLight(color=[1.0, 1.0, 1.0], intensity=12.0)
        self.scene.add(back_light, pose=self._look_at_origin([0, self.radius*3, -self.radius*2]))

    def _look_at_origin(self, position):
        """Helper to create a transform matrix looking at origin."""
        target = np.zeros(3)
        eye = np.array(position)
        up = np.array([0, 0, 1])
        
        z = (eye - target)
        z /= np.linalg.norm(z)
        x = np.cross(up, z)
        x /= np.linalg.norm(x)
        y = np.cross(z, x)
        
        m = np.eye(4)
        m[:3, 0] = x
        m[:3, 1] = y
        m[:3, 2] = z
        m[:3, 3] = eye
        return m