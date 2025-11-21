from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ConcurrencyOrchestratorAgent:
    def __init__(self, name: str = "并发编排专家"):
        self.name = name

    async def plan_batches(self, work_packages: List[Dict[str, Any]], software_units: List[Dict[str, Any]]) -> Dict[str, Any]:
        # 构建简单依赖图：按 context 分组，默认不同 context 可并行
        context_map: Dict[str, List[Dict[str, Any]]] = {}
        for p in work_packages:
            ctx = self._infer_context(p, software_units)
            context_map.setdefault(ctx, []).append(p)

        # 冲突检测：DB 迁移同表互斥；共享资源锁定
        conflicts: Dict[str, List[str]] = {}
        batches: List[List[str]] = []

        # 每个context形成一个批次，内部按包大小排序
        for ctx, pkgs in context_map.items():
            pkgs.sort(key=lambda x: len(x.get("software_unit_ids", [])))
            batch_ids = []
            locked_resources: set[str] = set()
            for p in pkgs:
                uids = p.get("software_unit_ids", [])
                resources = {uid for uid in uids if uid.startswith("DB::")}
                if locked_resources & resources:
                    conflicts[p["id"]] = list(locked_resources & resources)
                    continue
                locked_resources |= resources
                batch_ids.append(p["id"])
            if batch_ids:
                batches.append(batch_ids)

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

