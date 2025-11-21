from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class SoftwareUnitExtractorAgent:
    def __init__(self, name: str = "软件单元抽取专家"):
        self.name = name

    async def extract(self, architecture_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        units: List[Dict[str, Any]] = []

        system_arch = architecture_analysis.get("system_architecture", {})
        db_design = architecture_analysis.get("database_design", {})
        api_arch = architecture_analysis.get("api_architecture", {})

        components = system_arch.get("system_components", [])
        for comp in components:
            if isinstance(comp, dict):
                name = comp.get("name") or comp.get("component") or str(comp)
                context = comp.get("context") or comp.get("service") or "system"
                description = comp.get("description") or ""
            else:
                name = str(comp)
                context = "system"
                description = ""
            units.append({
                "id": f"COMP::{name}",
                "type": "component",
                "name": name,
                "context": context,
                "dependencies": [],
                "risk_level": self._infer_risk(description or name)
            })

        tables = db_design.get("tables", [])
        for tbl in tables:
            if isinstance(tbl, dict):
                name = tbl.get("name") or str(tbl)
                description = tbl.get("description") or ""
            else:
                name = str(tbl)
                description = ""
            units.append({
                "id": f"DB::{name}",
                "type": "db",
                "name": name,
                "context": db_design.get("database_type", "database"),
                "dependencies": [],
                "risk_level": self._infer_risk(description or name)
            })

        endpoints = api_arch.get("api_endpoints", [])
        for ep in endpoints:
            if isinstance(ep, dict):
                path = ep.get("path") or ep.get("url") or str(ep)
                method = ep.get("method") or "GET"
                name = f"{method} {path}"
                description = ep.get("description") or ""
            else:
                name = str(ep)
                description = ""
            units.append({
                "id": f"API::{name}",
                "type": "api",
                "name": name,
                "context": api_arch.get("api_style", "api"),
                "dependencies": [],
                "risk_level": self._infer_risk(description or name)
            })

        normalized = self._dedupe(units)
        logger.info(f"[{self.name}] 抽取到软件单元 {len(normalized)} 个")
        return normalized

    def _dedupe(self, units: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        result: List[Dict[str, Any]] = []
        for u in units:
            key = f"{u.get('type')}::{u.get('name')}::{u.get('context')}"
            if key in seen:
                continue
            seen.add(key)
            result.append(u)
        return result

    def _infer_risk(self, text: str) -> str:
        t = (text or "").lower()
        if any(k in t for k in ["payment", "security", "认证", "授权", "加密"]):
            return "high"
        if any(k in t for k in ["order", "数据库", "迁移", "索引"]):
            return "medium"
        return "low"

