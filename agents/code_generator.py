
from typing import List, Dict, Any
from agents.base_agent import BaseAgent
from config import DEV_MODEL

class CodeGeneratorAgent(BaseAgent):
    def __init__(self, name: str = "业务代码生成专家", model_config_name: str = "code_generator"):
        super().__init__(name=name, model_config_name=model_config_name, model_name=DEV_MODEL)

    async def generate(self, software_units: List[Dict[str, Any]], work_packages: List[Dict[str, Any]], output_dir: str) -> Dict[str, Any]:
        import os
        import json
        import re
        import asyncio
        
        base = os.path.join(output_dir, "project_code")
        
        # 离线逻辑
        if not getattr(self, "model", None):
            return {"generated_files": [], "note": "Offline mode, skipped"}

        generated_files = []
        
        # 1. 确保基础目录结构存在
        app_dir = os.path.join(base, "app")
        os.makedirs(app_dir, exist_ok=True)
        # 确保 app 包可被导入
        with open(os.path.join(app_dir, "__init__.py"), "w") as f: f.write("")

        # 分阶段生成：先生成模型和数据库，再生成服务，最后生成 Main
        # Phase 1: Models & Database
        tasks_phase1 = []
        
        api_units = [u for u in software_units if u.get("type") == "api"]
        comp_units = [u for u in software_units if u.get("type") == "component"]
        db_units = [u for u in software_units if u.get("type") == "db"]
        
        if db_units:
            prompt = f"""
            请根据以下数据库单元定义，生成 SQLAlchemy ORM 模型代码。
            
            【数据库单元】
            {json.dumps(db_units, ensure_ascii=False, indent=2)}
            
            【要求】
            1. 严禁使用Markdown标记。仅返回代码。
            2. 使用 SQLAlchemy Declarative Base。
            3. 定义 Base = declarative_base()。
            4. 定义具体的 Model 类。
            """
            tasks_phase1.append(self._generate_file(prompt, os.path.join(app_dir, "models.py"), generated_files))
            
            db_prompt = """
            生成一个标准的 database.py 文件。
            
            【要求】
            1. 严禁使用Markdown标记。仅返回代码。
            2. 定义 SessionLocal, engine, Base。
            3. 定义 get_db 依赖函数。
            4. 使用 sqlite:///./sql_app.db 作为默认连接。
            """
            tasks_phase1.append(self._generate_file(prompt, os.path.join(app_dir, "database.py"), generated_files))

        if tasks_phase1:
            await asyncio.gather(*tasks_phase1)

        # Phase 2: Services
        tasks_phase2 = []
        services_dir = os.path.join(app_dir, "services")
        os.makedirs(services_dir, exist_ok=True)
        with open(os.path.join(services_dir, "__init__.py"), "w") as f: f.write("")
            
        for unit in comp_units:
            prompt = f"""
            请根据以下组件单元定义，生成**功能完整**的业务逻辑类代码。
            
            【组件单元】
            {json.dumps(unit, ensure_ascii=False, indent=2)}
            
            【要求】
            1. 严禁使用Markdown标记。仅返回代码。
            2. 定义类和方法，**必须实现具体的业务逻辑**，严禁使用 `pass`。
            3. 如果涉及 CRUD，请使用内存字典模拟，或生成简单的数据库操作代码。
            4. 确保类名与单元名称一致（驼峰命名）。
            """
            
            safe_name = unit['name'].replace(" ", "_").lower()
            if not safe_name.endswith(".py"):
                safe_name += ".py"
            
            tasks_phase2.append(self._generate_file(prompt, os.path.join(services_dir, safe_name), generated_files))
            
        if tasks_phase2:
            await asyncio.gather(*tasks_phase2)

        # Phase 3: Main API
        tasks_phase3 = []
        if api_units:
            service_modules = []
            if os.path.exists(services_dir):
                service_modules = [f[:-3] for f in os.listdir(services_dir) if f.endswith(".py") and f != "__init__.py"]

            prompt = f"""
            请根据以下 API 单元定义，生成**完整可运行**的 FastAPI 入口文件 main.py。
            
            【API单元】
            {json.dumps(api_units, ensure_ascii=False, indent=2)}
            
            【已生成的服务模块 (app.services)】
            {json.dumps(service_modules, ensure_ascii=False, indent=2)}
            
            【要求】
            1. 严禁使用Markdown标记。仅返回代码。
            2. 包含 FastAPI 实例 app。
            3. **必须实现完整的路由处理函数**，包含真实的请求处理逻辑，严禁使用 pass 或 占位符。
            4. **显式导入**并使用上述服务模块中的类。
               - 例如: `from app.services.user_service import UserService`
            5. 必须包含 create_app 工厂函数（如果有需要）。
            6. 确保包含 /health 路由。
            """
            tasks_phase3.append(self._generate_file(prompt, os.path.join(app_dir, "main.py"), generated_files))
            
        if tasks_phase3:
            await asyncio.gather(*tasks_phase3)

        return {"generated_files": generated_files}
        
    async def repair(self, output_dir: str, error_log: str) -> Dict[str, Any]:
        """
        根据错误日志修复代码
        """
        import os
        import re
        import asyncio
        
        # 简单实现：尝试分析错误日志中提到的文件，并重新生成
        # 1. 从错误日志中提取文件名
        # 常见的 pytest 错误格式: File "/path/to/file.py", line 123
        files_to_fix = set()
        base = os.path.join(output_dir, "project_code")
        
        matches = re.findall(r'File "([^"]+)"', error_log)
        for path in matches:
            if base in path:
                rel_path = os.path.relpath(path, base)
                # 扩大修复范围：修复 app/ 下的代码，也修复 tests/ 下的代码（如果语法错误）
                if rel_path.startswith("app/") or rel_path.startswith("tests/"):
                    files_to_fix.add(rel_path)
        
        if not files_to_fix:
            print("未在错误日志中发现可修复的代码文件")
            return {"repaired": False}
            
        print(f"尝试修复文件: {files_to_fix}")
        
        repaired_files = []
        tasks = []
        
        for rel_path in files_to_fix:
            full_path = os.path.join(base, rel_path)
            if not os.path.exists(full_path):
                continue
                
            with open(full_path, "r", encoding="utf-8") as f:
                original_code = f.read()
                
            prompt = f"""
            以下代码在运行测试时报错，请根据错误日志进行修复。
            
            【错误日志】
            {error_log[:2000]}
            
            【源代码: {rel_path}】
            ```python
            {original_code}
            ```
            
            【要求】
            1. 仅返回修复后的完整代码。
            2. 严禁使用 Markdown 标记。
            3. 保持原有逻辑，仅修复错误。
            """
            
            # 使用并发生成进行修复
            tasks.append(self._generate_file(prompt, full_path, repaired_files))
            
        if tasks:
            await asyncio.gather(*tasks)
            
        return {"repaired": True, "files": repaired_files}

    async def _generate_file(self, prompt: str, filepath: str, generated_list: List[str]):
        import re
        import os
        try:
            # 使用带重试和并发控制的 LLM 调用
            response = await self.call_llm_with_retry([{"role": "user", "content": prompt}])
            content = await self._process_model_response(response)
            
            code_match = re.search(r'```python\s*([\s\S]*?)\s*```', content)
            if code_match:
                content = code_match.group(1)
            else:
                 lines = content.split('\n')
                 content = '\n'.join([line for line in lines if not line.strip().startswith(('Here', 'This', '请', '注意', '以下'))])

            # 确保目录存在
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            generated_list.append(filepath)
        except Exception as e:
            print(f"代码生成失败 [{filepath}]: {e}")
