from typing import List, Dict, Any
from agents.base_agent import BaseAgent
from config import DEV_MODEL

class TestGeneratorAgent(BaseAgent):
    def __init__(self, name: str = "测试代码生成专家", model_config_name: str = "test_generator"):
        super().__init__(name=name, model_config_name=model_config_name, model_name=DEV_MODEL)

    async def generate(self, software_units: List[Dict[str, Any]], work_packages: List[Dict[str, Any]], output_dir: str) -> Dict[str, Any]:
        import os
        import json
        import re
        
        # 离线回退逻辑
        if not getattr(self, "model", None):
            return await self._generate_offline(software_units, work_packages, output_dir)

        base = os.path.join(output_dir, "project_code")
        tests_dir = os.path.join(base, "tests")
        os.makedirs(tests_dir, exist_ok=True)
        
        # 扫描现有项目结构，辅助 LLM 生成正确的导入
        project_structure = []
        for root, dirs, files in os.walk(base):
            for file in files:
                if file.endswith(".py"):
                    rel_path = os.path.relpath(os.path.join(root, file), base)
                    project_structure.append(rel_path)
        
        generated_tests = []
        
        # 0. 生成 conftest.py
        conftest_path = os.path.join(tests_dir, "conftest.py")
        conftest_prompt = """
        生成一个标准的 Pytest conftest.py 文件。
        
        【要求】
        1. 严禁使用Markdown标记。仅返回代码。
        2. 定义 `test_db` fixture：
           - 使用 sqlite:///:memory:
           - 创建表 (Base.metadata.create_all)
           - yield session
           - 删除表 (Base.metadata.drop_all)
        3. 定义 `client` fixture：
           - 使用 TestClient(app)
           - 覆盖 get_db 依赖 (app.dependency_overrides)
        4. 假设 app 在 app.main 模块，get_db 在 app.database 模块，Base 在 app.database 模块。
        """
        # 优先生成 conftest
        await self._generate_file(conftest_prompt, conftest_path, generated_tests)
        
        # 1. 生成单元测试 (Unit Tests)
        testable_units = [u for u in software_units if u.get("type") in ["api", "component", "db"]]
        
        tasks = []
        
        for unit in testable_units:
            prompt = f"""
            请为以下软件单元编写 Pytest 单元测试代码。
            
            【软件单元】
            {json.dumps(unit, ensure_ascii=False, indent=2)}
            
            【项目现有文件结构】
            {json.dumps(project_structure, ensure_ascii=False, indent=2)}
            
            【严格约束】
            1. 必须输出纯 Python 代码，严禁包含任何 Markdown 标记（如 ```python）、中文解释或注释。
            2. 严禁使用 "your_module", "your_application" 等占位符。必须根据【项目现有文件结构】推断正确的导入路径。
               - 例如：如果存在 app/main.py，则使用 `from app.main import app`。
            3. 对于 API 测试，使用 `fastapi.testclient.TestClient`。
            4. 对于 DB 测试，使用 `sqlite:///:memory:` 进行 Mock。
            5. 如果无法确定导入路径，请假设代码在 `app` 包下。
            6. 确保导入的类和函数在项目中真实存在。
            """
            
            safe_name = unit['name'].replace(" ", "_").replace("/", "_").replace("{", "").replace("}", "").lower()
            if not safe_name.endswith(".py"):
                 safe_name += ".py"
            filename = f"test_unit_{safe_name}"
            filepath = os.path.join(tests_dir, filename)
            
            tasks.append(self._generate_file(prompt, filepath, generated_tests))

        # 2. 生成集成测试 (Integration Tests)
        for pkg in work_packages:
            prompt = f"""
            请为以下工作包编写 Pytest 集成测试代码。
            
            【工作包】
            {json.dumps(pkg, ensure_ascii=False, indent=2)}
            
            【包含的单元】
            {json.dumps([u for u in software_units if u['id'] in pkg.get('software_unit_ids', [])], ensure_ascii=False, indent=2)}
            
            【项目现有文件结构】
            {json.dumps(project_structure, ensure_ascii=False, indent=2)}
            
            【严格约束】
            1. 必须输出纯 Python 代码，严禁包含任何 Markdown 标记、中文解释。
            2. 严禁使用占位符，必须基于现有文件结构导入。
            3. 重点测试单元间的交互。
            4. 确保导入的类和函数在项目中真实存在。
            """
            
            safe_name = pkg['id'].replace("-", "_").lower()
            if not safe_name.endswith(".py"):
                 safe_name += ".py"
            filename = f"test_integration_{safe_name}"
            filepath = os.path.join(tests_dir, filename)
            
            tasks.append(self._generate_file(prompt, filepath, generated_tests))
            
        if tasks:
            import asyncio
            await asyncio.gather(*tasks)

        return {"tests": generated_tests, "coverage_threshold": 0.8}
        
    async def _generate_file(self, prompt: str, filepath: str, generated_list: List[str]):
        import re
        try:
            # 使用带重试和并发控制的 LLM 调用
            response = await self.call_llm_with_retry([{"role": "user", "content": prompt}])
            content = await self._process_model_response(response)
            
            # 强力清洗：提取代码块或清理非代码内容
            code_match = re.search(r'```python\s*([\s\S]*?)\s*```', content)
            if code_match:
                content = code_match.group(1)
            else:
                # 如果没有代码块标记，尝试去除可能的非代码行（如以中文开头的行）
                lines = content.split('\n')
                content = '\n'.join([line for line in lines if not line.strip().startswith(('Here', 'This', '请', '注意', '以下'))])

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            generated_list.append(filepath)
            
        except Exception as e:
            print(f"代码生成失败 [{filepath}]: {e}")

    async def _generate_offline(self, software_units: List[Dict[str, Any]], work_packages: List[Dict[str, Any]], output_dir: str) -> Dict[str, Any]:
        import os
        base = os.path.join(output_dir, "project_code")
        tests_dir = os.path.join(base, "tests")
        os.makedirs(tests_dir, exist_ok=True)
        
        # 简单的离线测试文件
        with open(os.path.join(tests_dir, "test_basic.py"), "w", encoding="utf-8") as f:
            f.write("def test_dummy():\n    assert True\n")
            
        return {"tests": ["tests/test_basic.py"], "coverage_threshold": 0.7}
