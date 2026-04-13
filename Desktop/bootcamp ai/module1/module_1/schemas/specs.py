"""
Module 1 — Schéma générique pour équipements mécaniques industriels.
Supporte : pompes, vannes, échangeurs, compresseurs, réducteurs, etc.
"""

from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ══════════════════════════════════════════════════════════════════
#  ENUMS
# ══════════════════════════════════════════════════════════════════

class EquipmentCategory(str, Enum):
    PUMP            = "pump"
    VALVE           = "valve"
    HEAT_EXCHANGER  = "heat_exchanger"
    COMPRESSOR      = "compressor"
    REDUCER         = "reducer"
    VESSEL          = "pressure_vessel"
    FILTER          = "filter"
    ACTUATOR        = "actuator"
    MOTOR           = "motor"
    UNKNOWN         = "unknown"


class EquipmentSubtype(str, Enum):
    # Pompes
    CENTRIFUGAL       = "centrifugal"
    AXIAL             = "axial"
    GEAR_PUMP         = "gear_pump"
    SCREW_PUMP        = "screw_pump"
    PISTON_PUMP       = "piston_pump"
    DIAPHRAGM_PUMP    = "diaphragm_pump"
    SUBMERSIBLE_PUMP  = "submersible_pump"
    # Vannes
    BALL_VALVE        = "ball_valve"
    GATE_VALVE        = "gate_valve"
    BUTTERFLY_VALVE   = "butterfly_valve"
    CHECK_VALVE       = "check_valve"
    GLOBE_VALVE       = "globe_valve"
    SAFETY_VALVE      = "safety_valve"
    # Echangeurs
    SHELL_TUBE        = "shell_and_tube"
    PLATE_EXCHANGER   = "plate_exchanger"
    AIR_COOLER        = "air_cooler"
    # Compresseurs
    RECIPROCATING     = "reciprocating"
    SCREW_COMPRESSOR  = "screw_compressor"
    CENTRIFUGAL_COMP  = "centrifugal_compressor"
    # Generique
    UNKNOWN           = "unknown"


class MaterialGrade(str, Enum):
    SS316L     = "316L"
    SS304      = "304"
    SS316      = "316"
    SS1_4462   = "1.4462"     # Duplex
    SS1_4408   = "1.4408"     # CF8M
    SS1_4571   = "1.4571"     # 316Ti
    CARBON     = "carbon_steel"
    CAST_IRON  = "cast_iron"
    BRONZE     = "bronze"
    HASTELLOY  = "hastelloy_c276"
    TITANIUM   = "titanium"
    ALUMINUM   = "aluminum"
    CAST_STEEL = "cast_steel"
    UNKNOWN    = "unknown"


class ConnectionType(str, Enum):
    FLANGED     = "flanged"
    THREADED    = "threaded"
    BUTT_WELD   = "butt_weld"
    SOCKET_WELD = "socket_weld"
    TRICLAMP    = "triclamp"
    VICTAULIC   = "victaulic"
    UNKNOWN     = "unknown"


class DriveType(str, Enum):
    ELECTRIC_MOTOR = "electric_motor"
    DIESEL_ENGINE  = "diesel_engine"
    STEAM_TURBINE  = "steam_turbine"
    PNEUMATIC      = "pneumatic"
    HYDRAULIC      = "hydraulic"
    MANUAL         = "manual"
    UNKNOWN        = "unknown"


class FluidType(str, Enum):
    WATER       = "water"
    CLEAN_WATER = "clean_water"
    SEAWATER    = "seawater"
    STEAM       = "steam"
    GAS         = "gas"
    OIL         = "oil"
    ACID        = "acid"
    SLURRY      = "slurry"
    CHEMICAL    = "chemical"
    UNKNOWN     = "unknown"


class MountingOrientation(str, Enum):
    HORIZONTAL = "horizontal"
    VERTICAL   = "vertical"
    INCLINED   = "inclined"
    UNKNOWN    = "unknown"


# ══════════════════════════════════════════════════════════════════
#  ALIAS — normalisation des sorties LLM
# ══════════════════════════════════════════════════════════════════

_CATEGORY_ALIASES = {
    "pump": "pump", "pompe": "pump", "centrifugal pump": "pump",
    "centrifugal": "pump", "pompe centrifuge": "pump",
    "valve": "valve", "vanne": "valve", "robinet": "valve",
    "heat exchanger": "heat_exchanger", "echangeur": "heat_exchanger",
    "compressor": "compressor", "compresseur": "compressor",
    "reducer": "reducer", "reducteur": "reducer",
    "vessel": "pressure_vessel", "cuve": "pressure_vessel",
    "filter": "filter", "filtre": "filter",
    "motor": "motor", "moteur": "motor",
}

_MATERIAL_ALIASES = {
    "ss316l": "316L", "316l": "316L", "316 l": "316L",
    "inox 316l": "316L", "aisi 316l": "316L", "1.4404": "316L",
    "ss316": "316", "316": "316",
    "ss304": "304", "304": "304", "aisi 304": "304", "1.4301": "304",
    "1.4408": "1.4408", "cf8m": "1.4408",
    "1.4462": "1.4462", "duplex": "1.4462",
    "1.4571": "1.4571", "316ti": "1.4571",
    "carbon steel": "carbon_steel", "carbon_steel": "carbon_steel",
    "acier carbone": "carbon_steel",
    "cast iron": "cast_iron", "cast_iron": "cast_iron", "fonte": "cast_iron",
    "bronze": "bronze",
    "hastelloy": "hastelloy_c276", "hastelloy c276": "hastelloy_c276",
    "titanium": "titanium", "titane": "titanium",
    "aluminum": "aluminum", "aluminium": "aluminum",
    "cast steel": "cast_steel", "acier moule": "cast_steel",
}

_FLUID_ALIASES = {
    "water": "water", "eau": "water",
    "clean water": "clean_water", "eau propre": "clean_water",
    "seawater": "seawater", "eau de mer": "seawater",
    "steam": "steam", "vapeur": "steam",
    "gas": "gas", "gaz": "gas",
    "oil": "oil", "huile": "oil",
    "acid": "acid", "acide": "acid",
    "slurry": "slurry", "boue": "slurry",
    "chemical": "chemical", "chimique": "chemical",
}


# ══════════════════════════════════════════════════════════════════
#  SUB-MODELS
# ══════════════════════════════════════════════════════════════════

class Dimensions(BaseModel):
    """Dimensions geometriques principales."""
    nominal_diameter_mm  : Optional[float] = None   # DN inlet
    outlet_diameter_mm   : Optional[float] = None   # DN outlet
    face_to_face_mm      : Optional[float] = None
    overall_length_mm    : Optional[float] = None
    overall_width_mm     : Optional[float] = None
    overall_height_mm    : Optional[float] = None
    weight_kg            : Optional[float] = None   # poids equipement seul
    weight_total_kg      : Optional[float] = None   # poids avec motorisation
    wall_thickness_mm    : Optional[float] = None
    bore_diameter_mm     : Optional[float] = None
    impeller_diameter_mm : Optional[float] = None   # pompes/compresseurs
    drawing_scale        : Optional[str]   = None   # ex "1:5"


class HydraulicSpec(BaseModel):
    """Performances hydrauliques et fluidiques."""
    nominal_pressure_bar : Optional[float] = None
    max_operating_bar    : Optional[float] = None
    test_pressure_bar    : Optional[float] = None
    pressure_class       : Optional[str]   = None   # PN16, ANSI 150#
    design_flow_m3h      : Optional[float] = None   # debit nominal
    max_flow_m3h         : Optional[float] = None
    min_flow_m3h         : Optional[float] = None
    design_head_m        : Optional[float] = None   # HMT pompes
    shutoff_head_m       : Optional[float] = None
    efficiency_pct       : Optional[float] = None   # rendement %
    npsh_required_m      : Optional[float] = None   # NPSH requis
    pump_speed_rpm       : Optional[float] = None
    max_flow_velocity_ms : Optional[float] = None


class TemperatureSpec(BaseModel):
    min_temp_celsius    : Optional[float] = None
    max_temp_celsius    : Optional[float] = None
    design_temp_celsius : Optional[float] = None


class ElectricalSpec(BaseModel):
    """Specifications de motorisation electrique."""
    rated_power_kw        : Optional[float] = None
    voltage_v             : Optional[float] = None
    frequency_hz          : Optional[float] = None
    rated_current_a       : Optional[float] = None
    motor_efficiency_class: Optional[str]   = None  # IE2, IE3
    motor_enclosure       : Optional[str]   = None  # IP55, ATEX
    number_of_poles       : Optional[int]   = None
    insulation_class      : Optional[str]   = None  # F, H


class ToleranceSpec(BaseModel):
    dimensional_tolerance : Optional[str]   = None
    surface_finish_ra     : Optional[float] = None
    leakage_class         : Optional[str]   = None
    acceptance_standard   : Optional[str]   = None  # ISO 9906, API 610


class SurfaceTreatment(BaseModel):
    coating        : Optional[str] = None
    paint_color    : Optional[str] = None   # ex "RAL 5002"
    internal_lining: Optional[str] = None


class ConnectionSpec(BaseModel):
    """Raccordements entree/sortie."""
    inlet_type      : ConnectionType = Field(ConnectionType.UNKNOWN)
    outlet_type     : ConnectionType = Field(ConnectionType.UNKNOWN)
    flange_standard : Optional[str]  = None   # EN1092-1, ASME B16.5
    bolt_standard   : Optional[str]  = None
    bolt_material   : Optional[str]  = None
    bolt_size       : Optional[str]  = None


class Certifications(BaseModel):
    standards : list[str] = Field(default_factory=list)
    markings  : list[str] = Field(default_factory=list)


class SealSpec(BaseModel):
    """Etancheite / garnitures mecaniques."""
    seal_type    : Optional[str] = None  # mechanical seal, packing, lip seal
    seal_material: Optional[str] = None
    seal_code    : Optional[str] = None  # ex Q1Q1X4GG
    sealing_plan : Optional[str] = None  # API plan 11, 52, 53


# ══════════════════════════════════════════════════════════════════
#  MAIN MODEL
# ══════════════════════════════════════════════════════════════════

class MechanicalEquipmentSpecs(BaseModel):
    """
    Specifications generiques extraites d'un plan technique
    d'equipement mecanique industriel.
    Compatible avec tous les modules avals (Module 2, 4, 6, 7, 9).
    """

    # Identification
    part_number     : Optional[str] = None
    revision        : Optional[str] = None
    drawing_number  : Optional[str] = None
    description     : Optional[str] = None
    manufacturer    : Optional[str] = None
    model_reference : Optional[str] = None

    # Classification
    equipment_category : EquipmentCategory   = Field(EquipmentCategory.UNKNOWN)
    equipment_subtype  : EquipmentSubtype    = Field(EquipmentSubtype.UNKNOWN)
    mounting           : MountingOrientation = Field(MountingOrientation.UNKNOWN)

    # Dimensions
    dimensions : Dimensions = Field(default_factory=Dimensions)

    # Performances
    hydraulics  : HydraulicSpec   = Field(default_factory=HydraulicSpec)
    temperature : TemperatureSpec = Field(default_factory=TemperatureSpec)

    # Materiaux
    body_material     : MaterialGrade = Field(MaterialGrade.UNKNOWN)
    impeller_material : Optional[str] = None
    shaft_material    : Optional[str] = None
    trim_material     : Optional[str] = None
    seal_material     : Optional[str] = None

    # Fluide
    fluid_type           : FluidType     = Field(FluidType.UNKNOWN)
    fluid_density_kg_m3  : Optional[float] = None
    fluid_viscosity_mm2s : Optional[float] = None

    # Connexions
    connections : ConnectionSpec = Field(default_factory=ConnectionSpec)

    # Motorisation
    drive_type : DriveType     = Field(DriveType.UNKNOWN)
    electrical : ElectricalSpec = Field(default_factory=ElectricalSpec)

    # Etancheite
    sealing : SealSpec = Field(default_factory=SealSpec)

    # Tolerances & finitions
    tolerances        : ToleranceSpec    = Field(default_factory=ToleranceSpec)
    surface_treatment : SurfaceTreatment = Field(default_factory=SurfaceTreatment)

    # Certifications
    certifications : Certifications = Field(default_factory=Certifications)

    # Contexte projet
    quantity_required : int = Field(200)

    # Meta-extraction
    extraction_confidence : float     = Field(0.0, ge=0.0, le=1.0)
    extraction_warnings   : list[str] = Field(default_factory=list)

    # Validators
    @field_validator("body_material", mode="before")
    @classmethod
    def normalize_material(cls, v):
        if v is None:
            return "unknown"
        return _MATERIAL_ALIASES.get(str(v).lower().strip(), "unknown")

    @field_validator("fluid_type", mode="before")
    @classmethod
    def normalize_fluid(cls, v):
        if v is None:
            return "unknown"
        return _FLUID_ALIASES.get(str(v).lower().strip(), str(v))

    @field_validator("equipment_category", mode="before")
    @classmethod
    def normalize_category(cls, v):
        if v is None:
            return "unknown"
        return _CATEGORY_ALIASES.get(str(v).lower().strip(), "unknown")

    class Config:
        use_enum_values = True


# ══════════════════════════════════════════════════════════════════
#  CONFIDENCE CALCULATOR
# ══════════════════════════════════════════════════════════════════

def compute_confidence(specs: MechanicalEquipmentSpecs) -> float:
    """
    Score de confiance objectif sur les champs critiques.
    10 criteres = 0.10 par critere satisfait.
    """
    checks = [
        specs.equipment_category != "unknown",
        specs.dimensions.nominal_diameter_mm is not None,
        specs.hydraulics.nominal_pressure_bar is not None,
        specs.body_material != "unknown",
        specs.fluid_type != "unknown",
        specs.connections.inlet_type != "unknown",
        specs.part_number is not None or specs.model_reference is not None,
        specs.certifications.standards != [],
        specs.hydraulics.design_flow_m3h is not None,
        specs.hydraulics.design_head_m is not None,
    ]
    return round(sum(checks) / len(checks), 2)


# ══════════════════════════════════════════════════════════════════
#  BACKWARD COMPATIBILITY
# ══════════════════════════════════════════════════════════════════
# Alias pour les modules qui importaient ValveSpecs directement
ValveSpecs = MechanicalEquipmentSpecs
