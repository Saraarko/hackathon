"""
Module 1 — Tests unitaires generalises pour MechanicalEquipmentSpecs.
Couverture cible : >= 60% sur les composants critiques.

Execution :
    pytest module_1/tests/ -v --cov=module_1 --cov-report=term-missing
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from module_1.parsers.pdf_parser import PDFParser, PDFParseError
from module_1.prompts.extraction_prompt import (
    build_extraction_prompt,
    build_tables_summary,
)
from module_1.schemas.specs import (
    MechanicalEquipmentSpecs,
    EquipmentCategory,
    EquipmentSubtype,
    MaterialGrade,
    FluidType,
    DriveType,
    compute_confidence,
    # Alias retro-compat
    ValveSpecs,
)
from module_1.schemas.state import ExtractionState
from module_1.agents.extraction_nodes import (
    node_parse_pdf,
    node_validate_specs,
    should_retry,
)
from module_1.outputs.writer import save_specs_json, load_specs_json


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_specs_pump() -> MechanicalEquipmentSpecs:
    """Specs pompe centrifuge KSB pour les tests (inspirees du PDF de reference)."""
    return MechanicalEquipmentSpecs(
        part_number="KSB-ETANORM-050-125",
        model_reference="Etanorm C 050-125 C10",
        manufacturer="KSB",
        equipment_category=EquipmentCategory.PUMP,
        equipment_subtype=EquipmentSubtype.CENTRIFUGAL,
        body_material=MaterialGrade.SS1_4408,
        fluid_type=FluidType.CLEAN_WATER,
        drive_type=DriveType.ELECTRIC_MOTOR,
        dimensions={
            "nominal_diameter_mm":  65.0,
            "outlet_diameter_mm":   50.0,
            "impeller_diameter_mm": 126.0,
        },
        hydraulics={
            "nominal_pressure_bar": 16.0,
            "design_flow_m3h":      76.0,
            "design_head_m":        15.0,
            "efficiency_pct":       77.1,
            "npsh_required_m":      3.70,
            "pump_speed_rpm":       2929.0,
            "shutoff_head_m":       20.0,
        },
        electrical={
            "rated_power_kw":          5.5,
            "voltage_v":               400.0,
            "frequency_hz":            50.0,
            "rated_current_a":         10.1,
            "motor_efficiency_class":  "IE2",
            "motor_enclosure":         "IP55",
            "number_of_poles":         2,
            "insulation_class":        "F",
        },
        connections={
            "inlet_type":      "flanged",
            "outlet_type":     "flanged",
            "flange_standard": "EN1092-1",
        },
        certifications={"standards": ["EN 733", "ISO 9906"], "markings": []},
        extraction_confidence=0.9,
    )


@pytest.fixture
def sample_specs_valve() -> MechanicalEquipmentSpecs:
    """Specs vanne DN100 PN40 pour tests retro-compatibilite."""
    return MechanicalEquipmentSpecs(
        part_number="VAN-DN100-PN40",
        equipment_category=EquipmentCategory.VALVE,
        equipment_subtype=EquipmentSubtype.BALL_VALVE,
        body_material=MaterialGrade.SS316L,
        dimensions={"nominal_diameter_mm": 100.0, "face_to_face_mm": 250.0},
        hydraulics={"nominal_pressure_bar": 40.0},
        connections={"inlet_type": "flanged", "flange_standard": "EN1092-1"},
        extraction_confidence=0.8,
    )


@pytest.fixture
def valid_json_pump(sample_specs_pump) -> str:
    """Reponse JSON valide simulant un retour LLM pour une pompe."""
    return json.dumps(sample_specs_pump.dict())


@pytest.fixture
def valid_json_valve(sample_specs_valve) -> str:
    """Reponse JSON valide simulant un retour LLM pour une vanne."""
    return json.dumps(sample_specs_valve.dict())


# ─────────────────────────────────────────────────────────────────────────────
# Tests Schema — MechanicalEquipmentSpecs
# ─────────────────────────────────────────────────────────────────────────────

class TestMechanicalEquipmentSpecs:

    def test_default_values(self):
        specs = MechanicalEquipmentSpecs()
        assert specs.equipment_category == EquipmentCategory.UNKNOWN.value
        assert specs.equipment_subtype == EquipmentSubtype.UNKNOWN.value
        assert specs.quantity_required == 200
        assert specs.extraction_confidence == 0.0
        assert specs.extraction_warnings == []

    def test_confidence_bounds(self):
        with pytest.raises(Exception):
            MechanicalEquipmentSpecs(extraction_confidence=1.5)
        with pytest.raises(Exception):
            MechanicalEquipmentSpecs(extraction_confidence=-0.1)

    def test_pump_specs_complete(self, sample_specs_pump):
        assert sample_specs_pump.equipment_category == "pump"
        assert sample_specs_pump.equipment_subtype == "centrifugal"
        assert sample_specs_pump.dimensions.nominal_diameter_mm == 65.0
        assert sample_specs_pump.hydraulics.design_flow_m3h == 76.0
        assert sample_specs_pump.hydraulics.design_head_m == 15.0
        assert sample_specs_pump.electrical.rated_power_kw == 5.5
        assert sample_specs_pump.electrical.motor_efficiency_class == "IE2"

    def test_valve_specs_compatible(self, sample_specs_valve):
        """Verifie la retro-compatibilite avec les specs de vanne."""
        assert sample_specs_valve.equipment_category == "valve"
        assert sample_specs_valve.dimensions.nominal_diameter_mm == 100.0
        assert sample_specs_valve.hydraulics.nominal_pressure_bar == 40.0

    def test_backward_compat_alias(self, sample_specs_valve):
        """ValveSpecs doit etre un alias de MechanicalEquipmentSpecs."""
        assert ValveSpecs is MechanicalEquipmentSpecs

    def test_material_normalization(self):
        specs = MechanicalEquipmentSpecs(body_material="AISI 316L")
        assert specs.body_material == "316L"

    def test_material_normalization_duplex(self):
        specs = MechanicalEquipmentSpecs(body_material="duplex")
        assert specs.body_material == "1.4462"

    def test_material_normalization_1_4408(self):
        specs = MechanicalEquipmentSpecs(body_material="1.4408")
        assert specs.body_material == "1.4408"

    def test_fluid_normalization(self):
        specs = MechanicalEquipmentSpecs(fluid_type="clean water")
        assert specs.fluid_type == "clean_water"

    def test_category_normalization_pump(self):
        specs = MechanicalEquipmentSpecs(equipment_category="pompe centrifuge")
        assert specs.equipment_category == "pump"

    def test_serialization_roundtrip(self, sample_specs_pump):
        raw = sample_specs_pump.json()
        reloaded = MechanicalEquipmentSpecs.parse_raw(raw)
        assert reloaded.part_number == sample_specs_pump.part_number
        assert reloaded.hydraulics.design_flow_m3h == sample_specs_pump.hydraulics.design_flow_m3h
        assert reloaded.electrical.rated_power_kw == sample_specs_pump.electrical.rated_power_kw


# ─────────────────────────────────────────────────────────────────────────────
# Tests Confidence Calculator
# ─────────────────────────────────────────────────────────────────────────────

class TestConfidenceCalculator:

    def test_empty_specs_low_confidence(self):
        specs = MechanicalEquipmentSpecs()
        score = compute_confidence(specs)
        assert score == 0.0

    def test_pump_full_specs_high_confidence(self, sample_specs_pump):
        score = compute_confidence(sample_specs_pump)
        assert score >= 0.8, f"Confiance trop basse pour specs pompe completes : {score}"

    def test_partial_specs_medium_confidence(self):
        specs = MechanicalEquipmentSpecs(
            equipment_category="pump",
            body_material="316L",
            hydraulics={"nominal_pressure_bar": 16.0, "design_flow_m3h": 50.0},
            dimensions={"nominal_diameter_mm": 65.0},
        )
        score = compute_confidence(specs)
        assert 0.2 < score < 0.9


# ─────────────────────────────────────────────────────────────────────────────
# Tests PDFParser
# ─────────────────────────────────────────────────────────────────────────────

class TestPDFParser:

    def test_raises_on_missing_file(self):
        with pytest.raises(PDFParseError, match="introuvable"):
            PDFParser("/non/existent/file.pdf")

    def test_raises_on_wrong_extension(self, tmp_path):
        txt_file = tmp_path / "plan.txt"
        txt_file.write_text("dummy")
        with pytest.raises(PDFParseError, match="Extension"):
            PDFParser(txt_file)

    def test_accepts_valid_pdf_path(self, tmp_path):
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")
        parser = PDFParser(pdf_file)
        assert parser.pdf_path == pdf_file

    @patch("module_1.parsers.pdf_parser._PDFPLUMBER_AVAILABLE", False)
    def test_returns_empty_string_without_pdfplumber(self, tmp_path):
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")
        parser = PDFParser(pdf_file)
        assert parser.extract_text() == ""
        assert parser.extract_tables() == []

    def test_clean_page_text_removes_short_lines(self):
        raw = "A\n\nEtanorm C 050-125 C10 Standardpump\n\nB"
        result = PDFParser._clean_page_text(raw)
        assert "Etanorm C 050-125" in result

    def test_normalize_table_returns_none_for_single_row(self):
        result = PDFParser._normalize_table([["col1", "col2"]], page_num=1)
        assert result is None

    def test_normalize_table_valid(self):
        table = [["DN", "PN", "Material"], ["65", "16", "1.4408"], ["50", "16", "1.4462"]]
        result = PDFParser._normalize_table(table, page_num=2)
        assert result is not None
        assert result["headers"] == ["DN", "PN", "Material"]
        assert len(result["rows"]) == 2


# ─────────────────────────────────────────────────────────────────────────────
# Tests Prompts
# ─────────────────────────────────────────────────────────────────────────────

class TestPrompts:

    def test_build_extraction_prompt_contains_text(self):
        prompt = build_extraction_prompt("Etanorm C 050-125 DN65 PN16 1.4408")
        assert "Etanorm" in prompt
        assert "json" in prompt.lower()

    def test_build_extraction_prompt_contains_new_fields(self):
        prompt = build_extraction_prompt("test")
        assert "equipment_category" in prompt
        assert "design_flow_m3h" in prompt
        assert "design_head_m" in prompt
        assert "electrical" in prompt
        assert "sealing" in prompt

    def test_build_extraction_prompt_truncates_long_text(self):
        long_text = "x" * 20_000
        prompt = build_extraction_prompt(long_text)
        assert "tronque" in prompt

    def test_build_tables_summary_empty(self):
        assert build_tables_summary([]) == ""

    def test_build_tables_summary_formats_correctly(self):
        tables = [{"page": 1, "headers": ["DN", "PN", "Flow"], "rows": [["65", "16", "76"]]}]
        summary = build_tables_summary(tables)
        assert "Tableau 1" in summary
        assert "DN" in summary
        assert "76" in summary


# ─────────────────────────────────────────────────────────────────────────────
# Tests Noeuds LangGraph
# ─────────────────────────────────────────────────────────────────────────────

class TestExtractionNodes:

    def test_node_parse_pdf_missing_file(self):
        state = ExtractionState(pdf_path="/nope/fake.pdf")
        result = node_parse_pdf(state)
        assert "errors" in result
        assert len(result["errors"]) > 0

    def test_node_validate_specs_valid_json_pump(self, valid_json_pump):
        state = ExtractionState(raw_llm_response=valid_json_pump)
        result = node_validate_specs(state)
        assert result.get("validation_passed") is True
        assert isinstance(result.get("specs"), MechanicalEquipmentSpecs)
        assert result["specs"].equipment_category == "pump"

    def test_node_validate_specs_valid_json_valve(self, valid_json_valve):
        state = ExtractionState(raw_llm_response=valid_json_valve)
        result = node_validate_specs(state)
        assert result.get("validation_passed") is True
        assert result["specs"].equipment_category == "valve"

    def test_node_validate_specs_invalid_json(self):
        state = ExtractionState(raw_llm_response="not valid json {{")
        result = node_validate_specs(state)
        assert not result.get("validation_passed", False)
        assert "errors" in result

    def test_node_validate_strips_markdown_fences(self, sample_specs_pump):
        wrapped = f"```json\n{sample_specs_pump.json()}\n```"
        state = ExtractionState(raw_llm_response=wrapped)
        result = node_validate_specs(state)
        assert result.get("validation_passed") is True

    def test_node_validate_adds_warnings_for_unknown_fields(self):
        minimal = json.dumps({
            "equipment_category": "unknown",
            "body_material": "unknown",
            "fluid_type": "unknown",
        })
        state = ExtractionState(raw_llm_response=minimal)
        result = node_validate_specs(state)
        assert result.get("validation_passed") is True
        assert len(result["specs"].extraction_warnings) > 0

    def test_should_retry_returns_end_on_success(self):
        state = ExtractionState(validation_passed=True)
        assert should_retry(state) == "end"

    def test_should_retry_returns_retry_when_attempts_remain(self):
        state = ExtractionState(validation_passed=False, parse_attempts=1)
        assert should_retry(state) == "retry"

    def test_should_retry_returns_end_when_max_attempts_reached(self):
        state = ExtractionState(validation_passed=False, parse_attempts=3)
        assert should_retry(state) == "end"


# ─────────────────────────────────────────────────────────────────────────────
# Tests Writer + compatibilite modules avals
# ─────────────────────────────────────────────────────────────────────────────

class TestWriter:

    def test_save_and_load_roundtrip(self, sample_specs_pump, tmp_path):
        saved_path = save_specs_json(sample_specs_pump, source_pdf="ksb_pump.pdf", output_dir=tmp_path)
        assert saved_path.exists()
        loaded = load_specs_json(saved_path)
        assert loaded.part_number == sample_specs_pump.part_number
        assert loaded.hydraulics.design_flow_m3h == sample_specs_pump.hydraulics.design_flow_m3h

    def test_saved_json_has_meta_v3(self, sample_specs_pump, tmp_path):
        saved_path = save_specs_json(sample_specs_pump, source_pdf="ksb_pump.pdf", output_dir=tmp_path)
        with open(saved_path) as f:
            data = json.load(f)
        assert "_meta" in data
        assert data["_meta"]["module"] == "module_1"
        assert data["_meta"]["schema_version"] == "3.0.0"
        assert data["_meta"]["equipment_type"] == "pump"

    def test_for_module2_has_cad_fields(self, sample_specs_pump, tmp_path):
        save_specs_json(sample_specs_pump, source_pdf="test.pdf", output_dir=tmp_path)
        files = list(tmp_path.glob("for_module2_*.json"))
        assert len(files) == 1
        with open(files[0]) as f:
            data = json.load(f)
        # Champs requis par le generateur DXF/IFC
        assert "equipment_category" in data
        assert "dimensions" in data
        assert "connections" in data
        assert data["dimensions"]["nominal_diameter_mm"] == 65.0
        assert data["dimensions"]["impeller_diameter_mm"] == 126.0
        assert data["connections"]["flange_standard"] == "EN1092-1"

    def test_for_module4_has_sourcing_fields(self, sample_specs_pump, tmp_path):
        save_specs_json(sample_specs_pump, source_pdf="test.pdf", output_dir=tmp_path)
        files = list(tmp_path.glob("for_module4_*.json"))
        assert len(files) == 1
        with open(files[0]) as f:
            data = json.load(f)
        # Champs requis par Wikidata / UN Comtrade
        assert data["body_material"] == "1.4408"
        assert data["fluid_type"] == "clean_water"
        assert data["nominal_pressure_bar"] == 16.0
        assert data["quantity"] == 200

    def test_for_module6_has_tco_fields(self, sample_specs_pump, tmp_path):
        save_specs_json(sample_specs_pump, source_pdf="test.pdf", output_dir=tmp_path)
        files = list(tmp_path.glob("for_module6_*.json"))
        assert len(files) == 1
        with open(files[0]) as f:
            data = json.load(f)
        # Champs requis pour le calcul TCO World Bank
        assert data["drive_type"] == "electric_motor"
        assert data["electrical"]["rated_power_kw"] == 5.5
        assert data["electrical"]["motor_efficiency_class"] == "IE2"
        assert data["hydraulics"]["design_flow_m3h"] == 76.0
        assert data["hydraulics"]["efficiency_pct"] == 77.1
        assert data["quantity"] == 200

    def test_output_dir_created_if_missing(self, sample_specs_pump, tmp_path):
        new_dir = tmp_path / "deep" / "nested" / "dir"
        saved_path = save_specs_json(sample_specs_pump, output_dir=new_dir)
        assert saved_path.exists()

    def test_valve_specs_also_saved_correctly(self, sample_specs_valve, tmp_path):
        """Verifie que les specs de vanne (cas historique) sont toujours sauvegardees."""
        saved_path = save_specs_json(sample_specs_valve, source_pdf="vanne.pdf", output_dir=tmp_path)
        with open(saved_path) as f:
            data = json.load(f)
        assert data["_meta"]["equipment_type"] == "valve"
        loaded = load_specs_json(saved_path)
        assert loaded.equipment_category == "valve"
        assert loaded.dimensions.nominal_diameter_mm == 100.0
