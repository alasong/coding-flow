from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ConcurrencyOrchestratorAgent:
    def __init__(self, name: str = "并发编排专家"):
        self.name = name

    async def plan_batches(self, work_packages: List[Dict[str, Any]], software_units: List[Dict[str, Any]]) -> Dict[str, Any]:
        pkg_map = {p["id"]: p for p in work_packages}
        pkg_ids = list(pkg_map.keys())
        deps_map: Dict[str, List[str]] = {}
        dependents: Dict[str, List[str]] = {pid: [] for pid in pkg_ids}

        for p in work_packages:
            deps = [d for d in p.get("depends_on", []) if d in pkg_map]
            deps_map[p["id"]] = deps
            for d in deps:
                dependents.setdefault(d, []).append(p["id"])

        in_degree = {pid: len(deps_map.get(pid, [])) for pid in pkg_ids}
        ready = sorted([pid for pid, deg in in_degree.items() if deg == 0])

        conflicts: Dict[str, List[str]] = {}
        batches: List[List[str]] = []
        scheduled: set[str] = set()

        while ready:
            batch_ids: List[str] = []
            locked_resources: set[str] = set()
            remaining: List[str] = []

            for pid in ready:
                pkg = pkg_map[pid]
                uids = pkg.get("software_unit_ids", [])
                resources = {uid for uid in uids if uid.startswith("DB::")}
                if locked_resources & resources:
                    conflicts[pid] = list(locked_resources & resources)
                    remaining.append(pid)
                    continue
                locked_resources |= resources
                batch_ids.append(pid)

            if not batch_ids and ready:
                batch_ids = [ready[0]]
                remaining = ready[1:]

            if batch_ids:
                batches.append(batch_ids)
                for pid in batch_ids:
                    scheduled.add(pid)
                    for nxt in dependents.get(pid, []):
                        in_degree[nxt] -= 1
                newly_ready = [pid for pid, deg in in_degree.items() if deg == 0 and pid not in scheduled and pid not in remaining]
                ready = sorted(remaining + newly_ready)
            else:
                break

        unscheduled = [pid for pid in pkg_ids if pid not in scheduled]
        if unscheduled:
            batches.append(unscheduled)

        plan = {
            "batches": batches,
            "conflicts": conflicts
        }
        logger.info(f"[{self.name}] 生成并发批次 {len(batches)}，冲突包 {len(conflicts)}")
        return plan

    def _infer_context(self, pkg: Dict[str, Any], software_units: List[Dict[str, Any]]) -> str:
        if pkg.get("software_unit_ids"):
            uid = pkg["software_unit_ids"][0]
            for u in software_units:
                if u["id"] == uid:
                    return u.get("context", "default")
        return "default"

