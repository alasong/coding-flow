from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class UnitToWorkPackageMatcherAgent:
    def __init__(self, name: str = "单元-工作包匹配专家"):
        self.name = name

    async def match(self, software_units: List[Dict[str, Any]], work_packages: List[Dict[str, Any]]) -> Dict[str, Any]:
        unit_index = {u["id"]: u for u in software_units}
        pkg_index = {p["id"]: p for p in work_packages}

        unbound_units: List[str] = []
        wrong_bindings: List[Dict[str, Any]] = []

        # 校验现有关联是否合理（按context/type一致性）
        for p in work_packages:
            valid_ids: List[str] = []
            for uid in p.get("software_unit_ids", []):
                u = unit_index.get(uid)
                if not u:
                    wrong_bindings.append({"package_id": p["id"], "unit_id": uid, "reason": "缺失的单元"})
                    continue
                if not self._is_coherent(p, u):
                    wrong_bindings.append({"package_id": p["id"], "unit_id": uid, "reason": "上下文/类型不一致"})
                    continue
                valid_ids.append(uid)
            p["software_unit_ids"] = valid_ids

        # 为未绑定单元寻找候选包
        bound_units = set(uid for p in work_packages for uid in p.get("software_unit_ids", []))
        for uid, u in unit_index.items():
            if uid in bound_units:
                continue
            candidates = [p for p in work_packages if self._is_coherent(p, u)]
            if candidates:
                # 选择当前负载最小的包
                candidates.sort(key=lambda x: len(x.get("software_unit_ids", [])))
                candidates[0].setdefault("software_unit_ids", []).append(uid)
            else:
                unbound_units.append(uid)

        logger.info(f"[{self.name}] 匹配完成，未绑定单元 {len(unbound_units)}，异常绑定 {len(wrong_bindings)}")
        return {
            "work_packages": work_packages,
            "unbound_units": unbound_units,
            "wrong_bindings": wrong_bindings
        }

    def _is_coherent(self, pkg: Dict[str, Any], unit: Dict[str, Any]) -> bool:
        # 基于 context/type 的简单一致性判断
        key = f"{unit.get('context','')}/{unit.get('type','')}"
        return pkg.get("name", "").startswith(key)

