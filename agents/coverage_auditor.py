from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class CoverageAuditorAgent:
    def __init__(self, name: str = "覆盖度审计专家"):
        self.name = name

    async def audit(self, software_units: List[Dict[str, Any]], work_packages: List[Dict[str, Any]]) -> Dict[str, Any]:
        unit_ids = {u["id"] for u in software_units}
        covered = set()
        duplicates: Dict[str, int] = {}

        for p in work_packages:
            for uid in p.get("software_unit_ids", []):
                if uid in covered:
                    duplicates[uid] = duplicates.get(uid, 1) + 1
                covered.add(uid)

        uncovered = sorted(list(unit_ids - covered))
        duplicate_list = sorted([{"unit_id": uid, "count": cnt} for uid, cnt in duplicates.items() if cnt > 1], key=lambda x: x["unit_id"]) 

        report = {
            "total_units": len(unit_ids),
            "covered_units": len(covered),
            "coverage_percentage": (len(covered) / len(unit_ids) * 100) if unit_ids else 0.0,
            "uncovered_units": uncovered,
            "duplicate_coverage": duplicate_list
        }

        logger.info(f"[{self.name}] 覆盖度: {report['coverage_percentage']:.2f}%，未覆盖 {len(uncovered)}")
        return report

