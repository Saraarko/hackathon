from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def run(
    pdf_path,
    llm_client: Any,
    save_output: bool = True,
    output_dir=None,
):
    from module_1.agents.graph import build_graph
    from module_1.outputs.writer import save_specs_json
    from module_1.schemas.state import ExtractionState

    logger.info("=" * 60)
    logger.info("[Module 1] Demarrage extraction — %s", pdf_path)
    logger.info("=" * 60)

    graph      = build_graph(llm_client=llm_client)
    init_state = ExtractionState(pdf_path=str(pdf_path))
    result     = graph.invoke(init_state)

    # LangGraph retourne un dict ou un dataclass selon la version
    if isinstance(result, dict):
        errors            = result.get("errors", [])
        validation_passed = result.get("validation_passed", False)
        specs             = result.get("specs", None)
    else:
        errors            = result.errors
        validation_passed = result.validation_passed
        specs             = result.specs

    if errors:
        for err in errors:
            logger.warning("  -- %s", err)

    if not validation_passed or specs is None:
        logger.error("[Module 1] ECHEC — aucune spec produite")
        return None

    logger.info("[Module 1] OK — categorie=%s / subtype=%s / DN=%.0f / corps=%s",
        specs.equipment_category,
        specs.equipment_subtype,
        specs.dimensions.nominal_diameter_mm or 0,
        specs.body_material,
    )

    if save_output:
        out       = Path(output_dir) if output_dir else None
        json_path = save_specs_json(specs, source_pdf=str(Path(pdf_path).name), output_dir=out)
        logger.info("[Module 1] JSON : %s", json_path)

    return specs
