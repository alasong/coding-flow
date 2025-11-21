import asyncio
from typing import Dict, Any
from fastapi import FastAPI, Body
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import os

from workflow.master_workflow import MasterWorkflow
from workflow.requirement_workflow import RequirementAnalysisWorkflow
from workflow.architecture_workflow import ArchitectureDesignWorkflow
from workflow.development_workflow import ProjectDevelopmentWorkflow
from workflow.development_execution_workflow import DevelopmentExecutionWorkflow
from workflow.deployment_workflow import DeploymentWorkflow
from config import OUTPUT_DIR, MASTER_WORKFLOW_CONFIG
from infra.persistence import save_task_summary, load_task_summary, save_task_detail
from infra.queue import TaskQueue
from utils.common import get_project_slug

app = FastAPI()

tasks: Dict[str, Any] = {}
TASKS_FILE = os.path.join(OUTPUT_DIR, "tasks_index.json")

def _save_tasks():
    try:
        save_task_summary(OUTPUT_DIR, tasks)
    except Exception:
        pass

def _load_tasks():
    try:
        loaded = load_task_summary(OUTPUT_DIR)
        for tid, meta in loaded.items():
            t = tasks.setdefault(tid, {})
            t.update(meta)
    except Exception:
        pass

_load_tasks()
ws_clients = set()

app.mount("/ui", StaticFiles(directory="dashboard", html=True), name="ui")
# 暴露输出文件目录，便于界面直接访问报告与工件
app.mount("/files", StaticFiles(directory=OUTPUT_DIR, html=False), name="files")


def _new_task_progress() -> Dict[str, Any]:
    return {
        "status": "running",
        "project_dir": None,
        "steps": {
            "requirement_analysis": {"status": "pending"},
            "architecture_design": {"status": "pending"},
            "decomposition": {"status": "pending"},
            "development_execution": {"status": "pending"},
            "deployment": {"status": "pending"},
        }
    }

async def run_pipeline(task_id: str, input_text: str):
    project_slug = get_project_slug(input_text)
    # 保证不同任务目录唯一
    import uuid
    unique_suffix = uuid.uuid4().hex[:6]
    project_output_dir = os.path.join(OUTPUT_DIR, f"{project_slug}-{unique_suffix}")
    os.makedirs(project_output_dir, exist_ok=True)
    mw = MasterWorkflow()
    mw.context["project_output_dir"] = project_output_dir

    if MASTER_WORKFLOW_CONFIG.get("enable_requirement_workflow", True):
        tasks[task_id]["steps"]["requirement_analysis"]["status"] = "running"
        req = RequirementAnalysisWorkflow()
        req_result = await req.run(input_text, output_dir=project_output_dir)
        mw.context["requirement_analysis"] = req_result
        tasks[task_id].setdefault("results", {})["requirement_analysis"] = req_result
        tasks[task_id]["steps"]["requirement_analysis"]["status"] = "completed"
        _save_tasks()

    if MASTER_WORKFLOW_CONFIG.get("enable_architecture_workflow", True):
        tasks[task_id]["steps"]["architecture_design"]["status"] = "running"
        arch = ArchitectureDesignWorkflow()
        req_result = mw.context.get("requirement_analysis", {})
        if "results" in req_result and "requirement_items" in req_result["results"]:
            architecture_input = req_result["results"]["requirement_items"]
        else:
            architecture_input = req_result
        arch_result = await arch.run(architecture_input, output_dir=project_output_dir)
        mw.context["architecture_design"] = arch_result
        tasks[task_id].setdefault("results", {})["architecture_design"] = arch_result
        tasks[task_id]["steps"]["architecture_design"]["status"] = "completed"
        _save_tasks()

    if getattr(mw, "development_workflow", None):
        tasks[task_id]["steps"]["decomposition"]["status"] = "running"
        decomp = ProjectDevelopmentWorkflow()
        arch_ctx = mw.context.get("architecture_design", {})
        arch_final = arch_ctx.get("final_result", {})
        architecture_analysis = arch_final.get("architecture_design", {})
        development_result = await decomp.execute(architecture_analysis, output_dir=os.path.join(project_output_dir, "decomposition"))
        mw.context["decomposition"] = development_result
        tasks[task_id].setdefault("results", {})["decomposition"] = development_result
        tasks[task_id]["steps"]["decomposition"]["status"] = "completed"
        _save_tasks()

    if getattr(mw, "development_execution_workflow", None):
        tasks[task_id]["steps"]["development_execution"]["status"] = "running"
        devexec = DevelopmentExecutionWorkflow()
        devexec_result = await devexec.execute(
            mw.context.get("decomposition", {}),
            requirements=mw.context.get("requirement_analysis", {}),
            architecture=mw.context.get("architecture_design", {}),
            output_dir=os.path.join(project_output_dir, "development_execution")
        )
        mw.context["development_execution"] = devexec_result
        tasks[task_id].setdefault("results", {})["development_execution"] = devexec_result
        tasks[task_id]["steps"]["development_execution"]["status"] = "completed"
        _save_tasks()

    if MASTER_WORKFLOW_CONFIG.get("enable_deployment_workflow", True):
        tasks[task_id]["steps"]["deployment"]["status"] = "running"
        deploy = DeploymentWorkflow()
        deploy_result = await deploy.execute(
            mw.context.get("development_execution", {}),
            requirements=mw.context.get("requirement_analysis", {}),
            architecture=mw.context.get("architecture_design", {}),
            output_dir=os.path.join(project_output_dir, "deployment")
        )
        mw.context["deployment"] = deploy_result
        tasks[task_id].setdefault("results", {})["deployment"] = deploy_result
        tasks[task_id]["steps"]["deployment"]["status"] = "completed"
        _save_tasks()

    tasks[task_id]["project_dir"] = project_output_dir
    dep = tasks[task_id].get("results", {}).get("deployment", {})
    env = dep.get("final_result", {}).get("env")
    if env:
        tasks[task_id]["env"] = env
    tasks[task_id]["status"] = "completed"
    _save_tasks()
    # 保存详细状态到项目目录
    try:
        save_task_detail(project_output_dir, tasks[task_id])
    except Exception:
        pass


@app.post("/run")
async def run(input_text: str = Body(..., embed=True)):
    import uuid
    task_id = uuid.uuid4().hex[:8]
    tasks[task_id] = _new_task_progress()
    _save_tasks()
    # 使用队列执行
    await queue.enqueue({"task_id": task_id, "input_text": input_text})
    return {"status": "started", "task_id": task_id}


@app.get("/status")
async def status():
    if not tasks:
        _load_tasks()
    return {"tasks": {tid: {"status": t.get("status"), "project_dir": t.get("project_dir")} for tid, t in tasks.items()}}

@app.get("/status/{task_id}")
async def status_one(task_id: str):
    t = tasks.get(task_id)
    if t and t.get("project_dir"):
        try:
            # 合并持久化的详细数据
            from infra.persistence import load_task_detail
            detail = load_task_detail(t["project_dir"])
            merged = {**t, **detail}
            return merged
        except Exception:
            return t
    return tasks.get(task_id, {"error": "not_found"})


@app.get("/results/{task_id}")
async def results(task_id: str):
    return tasks.get(task_id, {}).get("results", {})

@app.get("/metrics/{task_id}")
async def metrics(task_id: str):
    t = tasks.get(task_id, {})
    r = t.get("results", {})
    decomp = r.get("decomposition", {})
    devexec = r.get("development_execution", {})
    cov = decomp.get("steps", {}).get("coverage", {})
    wp = decomp.get("steps", {}).get("work_packages", {})
    conc = decomp.get("steps", {}).get("concurrency", {})
    env = devexec.get("final_result", {}).get("env", {})
    return {
        "coverage": cov.get("coverage_percentage"),
        "work_packages": wp.get("count"),
        "batches": len(conc.get("batches", [])) if conc else None,
        "compose_started": env.get("compose_started"),
        "ui_url": env.get("ui_url"),
        "health_url": env.get("health_url")
    }

@app.get("/details/{task_id}")
async def details(task_id: str):
    t = tasks.get(task_id, {})
    project_dir = t.get("project_dir")
    if not project_dir:
        return {"error": "not_found"}
    # 计算文件基路径（/files/...）
    rel = os.path.relpath(project_dir, OUTPUT_DIR).replace("\\", "/")
    file_base = f"/files/{rel}"
    r = t.get("results", {})
    devexec = r.get("development_execution", {})
    scaffold = devexec.get("final_result", {}).get("scaffold", {})
    code_dir = scaffold.get("code_dir")
    code_rel = None
    if code_dir:
        code_rel = os.path.relpath(code_dir, OUTPUT_DIR).replace("\\", "/")
    deploy_dir = os.path.join(project_dir, "deployment")
    deploy_rel = os.path.relpath(deploy_dir, OUTPUT_DIR).replace("\\", "/") if os.path.exists(deploy_dir) else None
    return {
        "file_base": file_base,
        "project_dir": project_dir,
        "code_dir": code_rel and f"/files/{code_rel}",
        "deployment_dir": deploy_rel and f"/files/{deploy_rel}",
        "reports_dir": deploy_rel and f"/files/{deploy_rel}/reports",
        "env": t.get("env", {}),
        "metrics": await metrics(task_id)
    }


# 初始化队列与工作协程
queue = TaskQueue(worker_count=2)

@app.on_event("startup")
async def startup_event():
    async def handler(item: dict):
        await run_pipeline(item["task_id"], item["input_text"])
    await queue.start(handler)
    asyncio.create_task(_periodic_broadcast())


async def _periodic_broadcast():
    while True:
        try:
            if ws_clients:
                import json
                payload = {"type": "tasks", "data": {"tasks": {tid: {"status": t.get("status"), "project_dir": t.get("project_dir")} for tid, t in tasks.items()}}}
                for ws in list(ws_clients):
                    try:
                        await ws.send_text(json.dumps(payload))
                    except Exception:
                        try:
                            ws_clients.discard(ws)
                        except Exception:
                            pass
        except Exception:
            pass
        await asyncio.sleep(2)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    ws_clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_clients.discard(ws)


@app.post("/deploy/start/{task_id}")
async def deploy_start(task_id: str):
    t = tasks.get(task_id)
    if not t:
        return {"error": "not_found"}
    dep = t.get("results", {}).get("deployment", {})
    out = dep.get("final_result", {}).get("output_dir")
    docker_dir = os.path.join(out, "docker") if out else None
    if docker_dir and os.path.exists(os.path.join(docker_dir, "docker-compose.yml")):
        try:
            import subprocess
            subprocess.run("docker compose up -d", cwd=docker_dir, shell=True, check=False)
            # 保留部署后的环境入口
            env = dep.get("final_result", {}).get("env", {})
            env["compose_started"] = True
            t["env"] = env
        except Exception:
            subprocess.run("docker-compose up -d", cwd=docker_dir, shell=True, check=False)
            env = dep.get("final_result", {}).get("env", {})
            env["compose_started"] = True
            t["env"] = env
        return {"status": "started", "env": t.get("env", {})}
    return {"error": "compose_not_found"}


@app.post("/deploy/stop/{task_id}")
async def deploy_stop(task_id: str):
    t = tasks.get(task_id)
    if not t:
        return {"error": "not_found"}
    dep = t.get("results", {}).get("deployment", {})
    out = dep.get("final_result", {}).get("output_dir")
    docker_dir = os.path.join(out, "docker") if out else None
    if docker_dir and os.path.exists(os.path.join(docker_dir, "docker-compose.yml")):
        try:
            import subprocess
            subprocess.run("docker compose down", cwd=docker_dir, shell=True, check=False)
            env = dep.get("final_result", {}).get("env", {})
            env["compose_started"] = False
            t["env"] = env
        except Exception:
            subprocess.run("docker-compose down", cwd=docker_dir, shell=True, check=False)
            env = dep.get("final_result", {}).get("env", {})
            env["compose_started"] = False
            t["env"] = env
        return {"status": "stopped"}
    return {"error": "compose_not_found"}
