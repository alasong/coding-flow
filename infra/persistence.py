import os
import json
from typing import Dict, Any


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def tasks_index_path(output_dir: str) -> str:
    return os.path.join(output_dir, "tasks_index.json")


def save_task_summary(output_dir: str, tasks: Dict[str, Any]) -> None:
    ensure_dir(output_dir)
    with open(tasks_index_path(output_dir), "w", encoding="utf-8") as f:
        json.dump({tid: {k: v for k, v in t.items() if k in ["status", "project_dir", "env"]}
                   for tid, t in tasks.items()}, f, ensure_ascii=False, indent=2)


def load_task_summary(output_dir: str) -> Dict[str, Any]:
    path = tasks_index_path(output_dir)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_task_detail(task_dir: str, detail: Dict[str, Any]) -> None:
    ensure_dir(task_dir)
    with open(os.path.join(task_dir, "status.json"), "w", encoding="utf-8") as f:
        json.dump(detail, f, ensure_ascii=False, indent=2)


def load_task_detail(task_dir: str) -> Dict[str, Any]:
    path = os.path.join(task_dir, "status.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

