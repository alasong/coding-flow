from typing import List, Dict, Any


class DBMigrationPlannerAgent:
    def __init__(self, name: str = "数据库迁移规划"):
        self.name = name

    async def plan(self, software_units: List[Dict[str, Any]], work_packages: List[Dict[str, Any]], output_dir: str) -> Dict[str, Any]:
        import os
        base = os.path.join(output_dir, "project_code", "migrations")
        os.makedirs(base, exist_ok=True)
        with open(os.path.join(base, "0001_init.sql"), "w", encoding="utf-8") as f:
            f.write("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username VARCHAR(50));\n")
        return {"migrations": ["migrations/0001_init.sql"], "conflicts": {}}
