
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
            service_class_map = {} # 模块名 -> 类名 的映射
            
            if os.path.exists(services_dir):
                for f in os.listdir(services_dir):
                    if f.endswith(".py") and f != "__init__.py":
                        module_name = f[:-3]
                        service_modules.append(module_name)
                        
                        # 尝试提取类名
                        try:
                            file_path = os.path.join(services_dir, f)
                            with open(file_path, "r", encoding="utf-8") as pyf:
                                content = pyf.read()
                                # 简单的正则提取类名 (寻找 class Xxx:)
                                import re
                                classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
                                if classes:
                                    # 假设第一个类就是主服务类
                                    service_class_map[module_name] = classes[0]
                        except Exception as e:
                            print(f"提取类名失败 [{f}]: {e}")

            prompt = f"""
            请根据以下 API 单元定义，生成**完整可运行**的 FastAPI 入口文件 main.py。
            
            【API单元】
            {json.dumps(api_units, ensure_ascii=False, indent=2)}
            
            【已生成的服务模块与类名映射】
            {json.dumps(service_class_map, ensure_ascii=False, indent=2)}
            
            【要求】
            1. 严禁使用Markdown标记。仅返回代码。
            2. 包含 FastAPI 实例 app。
            3. **必须实现完整的路由处理函数**，包含真实的请求处理逻辑，严禁使用 pass 或 占位符。
            4. **显式导入**并使用上述映射表中的类名。
               - 例如: 如果映射中有 "user_service": "UserService"，则必须 `from app.services.user_service import UserService`
            5. 必须包含 create_app 工厂函数（如果有需要）。
            6. 确保包含 /health 路由。
            """
            tasks_phase3.append(self._generate_file(prompt, os.path.join(app_dir, "main.py"), generated_files))
            
        if tasks_phase3:
            await asyncio.gather(*tasks_phase3)

        return {"generated_files": generated_files}
        
    async def repair(self, output_dir: str, error_log: str, skip_files: set[str] | None = None, max_files: int | None = None, architecture_design: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        根据错误日志修复代码（深度分析 + 精准修复 + 架构感知）
        """
        import os
        import asyncio
        import json
        
        # 兼容性处理：如果 output_dir 下有 project_code 则使用之，否则假设 output_dir 本身就是代码根目录
        project_code_dir = os.path.join(output_dir, "project_code")
        if os.path.exists(project_code_dir):
            base = project_code_dir
        else:
            base = output_dir
            
        skip_files = skip_files or set()
        
        # 1. 深度分析错误日志
        error_cases = self._analyze_error_log(error_log, base)
        
        # 2. 过滤与排序
        # 过滤掉已修复或不在项目目录的文件
        valid_cases = []
        for case in error_cases:
            if case['file_path'] in skip_files:
                continue
            if not os.path.exists(os.path.join(base, case['file_path'])):
                continue
            valid_cases.append(case)
            
        # 简单去重 (同一文件可能多次报错)
        unique_cases = {}
        for case in valid_cases:
            if case['file_path'] not in unique_cases:
                unique_cases[case['file_path']] = case
            else:
                # 合并错误信息
                unique_cases[case['file_path']]['error_message'] += "\n" + case['error_message']
        
        # 限制修复数量 (优先修复 SyntaxError/ImportError)
        files_to_fix = list(unique_cases.values())
        # 排序策略：SyntaxError > ImportError > AssertionError > Others
        def error_priority(case):
            etype = case['error_type']
            if 'SyntaxError' in etype: return 0
            if 'ImportError' in etype or 'ModuleNotFoundError' in etype: return 1
            if 'AttributeError' in etype: return 2
            if 'AssertionError' in etype: return 3
            return 4
            
        files_to_fix.sort(key=error_priority)
        
        if max_files is not None and max_files > 0:
            files_to_fix = files_to_fix[:max_files]
            
        if not files_to_fix:
            print("未发现需要修复的新文件")
            return {"repaired": False, "reason": "no_new_files", "files": []}
            
        print(f"尝试修复文件 (Top {len(files_to_fix)}): {[c['file_path'] for c in files_to_fix]}")
        
        repaired_files = []
        tasks = []
        
        # 准备架构上下文摘要 (如果有)
        arch_context = ""
        if architecture_design:
            try:
                # 提取关键组件信息
                components = architecture_design.get("final_result", {}).get("architecture_design", {}).get("system_architecture", {}).get("system_components", [])
                if not components:
                    # 尝试其他结构
                    components = architecture_design.get("system_components", [])
                
                if components:
                    arch_context = "【系统组件参考】\n"
                    for comp in components:
                        arch_context += f"- {comp.get('name')}: {comp.get('description')}\n"
                        if 'responsibilities' in comp:
                            arch_context += f"  职责: {', '.join(comp['responsibilities'])}\n"
            except Exception as e:
                print(f"提取架构上下文失败: {e}")

        for case in files_to_fix:
            rel_path = case['file_path']
            full_path = os.path.join(base, rel_path)
            
            with open(full_path, "r", encoding="utf-8") as f:
                original_code = f.read()
                
            # 构建上下文：读取关联文件 (例如测试对应的源文件，或源文件对应的测试)
            context_code = ""
            if case['related_files']:
                for rel_rel_path in case['related_files']:
                    full_rel_path = os.path.join(base, rel_rel_path)
                    if os.path.exists(full_rel_path):
                        with open(full_rel_path, "r") as rf:
                            context_code += f"\n# 相关文件: {rel_rel_path}\n{rf.read()[:1000]}\n..."
            
            # 智能提取特定组件的详细设计
            specific_comp_context = ""
            if architecture_design:
                # 简单的名称匹配
                filename = os.path.basename(rel_path).lower()
                for comp in components:
                    comp_name = comp.get('name', '').lower().replace(" ", "")
                    if comp_name in filename or filename.replace("test_", "").replace("unit_", "").startswith(comp_name):
                         specific_comp_context = f"【当前组件设计详情】\n{json.dumps(comp, ensure_ascii=False, indent=2)}\n"
                         break

            prompt = f"""
            以下代码在运行测试时报错，请根据错误日志和架构设计进行**精准修复**。
            
            {arch_context}
            {specific_comp_context}
            
            【错误类型】 {case['error_type']}
            【错误位置】 {rel_path}:{case.get('line_no', '?')}
            
            【错误详情】
            {case['error_message']}
            
            【源代码: {rel_path}】
            ```python
            {original_code}
            ```
            
            {context_code}
            
            【修复原则】
            1. **架构一致性**：必须遵循上述架构设计。如果代码实现与架构（如接口定义、依赖关系）不符，请修正代码以匹配架构。
            2. **Mock 优先**：如果是单元测试报错，优先检查 Mock 对象是否正确模拟了依赖组件的行为。不要试图去连接真实数据库或外部服务。
            3. **最小修改**：仅修复错误，不要重写无关逻辑。
            4. **完整性**：仅返回修复后的完整代码，不要包含 Markdown 标记。
            
            【针对性策略】
            - ImportError: 检查导入路径是否正确，或者被导入的模块是否确实存在定义。如果缺失定义，可能需要你根据组件设计来补全桩代码 (Stub)。
            - AssertionError: 检查业务逻辑是否满足测试期望。如果是测试期望有误（如与架构不符），请修正测试代码。
            """
            
            tasks.append(self._generate_file(prompt, full_path, repaired_files))
            
        if tasks:
            await asyncio.gather(*tasks)
            
        return {"repaired": True, "files": repaired_files}

    def _analyze_error_log(self, log: str, base_dir: str) -> List[Dict[str, Any]]:
        """
        解析 Pytest 日志，提取结构化错误信息
        """
        import re
        cases = []
        
        # 预处理：移除 ANSI 颜色代码，防止正则匹配失败
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        log = ansi_escape.sub('', log)
        
        # 策略 A: 匹配标准测试失败 (_________________ test_name _________________)
        blocks = re.split(r'_{10,}\s+test\w+\s+_{10,}', log)
        if len(blocks) > 1:
            # 第一块通常是 header，忽略
            for block in blocks[1:]:
                self._extract_error_from_block(block, base_dir, cases)
        
        # 策略 B: 匹配收集错误 (ERROR collecting tests/test_xxx.py)
        # 这种情况下，日志通常包含 "ERROR collecting ..." 和随后的 Traceback
        collect_errors = re.findall(r'ERROR collecting (.*?)\n(.*?)(?=\n={10,}|\nERROR collecting|\Z)', log, re.DOTALL)
        for file_path, traceback in collect_errors:
            # 尝试从 traceback 中找到具体的 SyntaxError 或 ImportError
            self._extract_error_from_block(f"File \"{file_path}\"\n{traceback}", base_dir, cases)

        # 策略 C: 如果上述都失败，尝试全局搜索 Traceback 模式
        if not cases:
            # 寻找所有的 "File "xxx", line nnn" 模式，并取最后几个
            # 这通常能捕获到 SyntaxError 或 ImportError 的堆栈
            self._extract_error_from_block(log, base_dir, cases)

        return cases

    def _extract_error_from_block(self, block: str, base_dir: str, cases: List[Dict[str, Any]]):
        import re
        import os
        
        # 提取文件路径和行号
        # 模式 1: 标准 Python Traceback (File "path", line 123)
        matches_std = re.findall(r'File "([^"]+)", line (\d+)', block)
        
        # 模式 2: Pytest short/no 模式 (path:123: in func)
        # 注意：排除 http:// 等 URL，只匹配文件路径
        matches_pytest = re.findall(r'([\w./-]+):(\d+):', block)
        
        file_matches = matches_std + matches_pytest
        
        if not file_matches:
            return

        # 寻找最相关的业务代码或测试代码
        target_file = None
        line_no = 0
        
        for fpath, lno in reversed(file_matches):
            # 处理 fpath，如果是绝对路径，尝试转相对
            if base_dir in fpath:
                rel = os.path.relpath(fpath, base_dir)
            else:
                rel = fpath
            
            # 清理可能的 ./ 前缀
            if rel.startswith("./"):
                rel = rel[2:]
                
            if rel.startswith("app/") or rel.startswith("tests/"):
                target_file = rel
                line_no = int(lno)
                break
        
        if not target_file:
            return
            
        # 提取错误类型
        error_type = "UnknownError"
        error_msg = block[-1000:] # 取最后一段作为详情
        
        # 常见的 Python 错误匹配
        # E   NameError: name 'x' is not defined
        # SyntaxError: invalid syntax
        # ImportError: cannot import name 'x'
        
        # 优先匹配 "E   Type: Msg"
        e_match = re.search(r'E\s+([\w\.]+(?:Error|Exception)): (.+)', block)
        if e_match:
            error_type = e_match.group(1)
            error_msg = e_match.group(2)
        else:
            # 匹配 "Type: Msg" (通常在 Traceback 底部)
            type_match = re.search(r'\n([A-Z]\w+Error): (.+)', block)
            if type_match:
                error_type = type_match.group(1)
                error_msg = type_match.group(2)

        # 关联文件推断
        related = []
        
        # 针对 ImportError 的增强分析
        # ImportError: cannot import name 'get_db' from 'app.database'
        if "ImportError" in error_type or "ModuleNotFoundError" in error_type:
            import_match = re.search(r"from '([\w\.]+)'", error_msg)
            if import_match:
                module_name = import_match.group(1)
                # 将模块名转换为路径: app.database -> app/database.py
                module_path = module_name.replace(".", "/") + ".py"
                related.append(module_path)
                
                # 关键策略：如果是项目内部文件，直接将其作为主要的修复目标！
                # 因为 ImportError 通常意味着被导入文件有问题
                if module_path.startswith("app/") or module_path.startswith("tests/"):
                    cases.append({
                        "file_path": module_path,
                        "line_no": 0,
                        "error_type": "DefinitionMissingError", # 自定义类型，提示缺失定义
                        "error_message": f"Module {module_name} missing required definitions (caused ImportError in {target_file})",
                        "related_files": []
                    })

        if target_file.startswith("tests/"):
            # 尝试从文件名推断: tests/test_unit_users.py -> app/services/users.py (仅示例)
            pass

        cases.append({
            "file_path": target_file,
            "line_no": line_no,
            "error_type": error_type,
            "error_message": error_msg,
            "related_files": related
        })

    async def _generate_file(self, prompt: str, filepath: str, generated_list: List[str]):
        import re
        import os
        import ast
        
        MAX_RETRIES = 3
        for attempt in range(MAX_RETRIES):
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

                # 静态语法检查 (Syntax Check Gate)
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    print(f"[Attempt {attempt+1}] 生成代码存在语法错误: {e}")
                    # 将错误反馈给 LLM 进行自我修正
                    prompt += f"\n\n上一轮生成的代码存在语法错误 (Line {e.lineno}: {e.msg})，请修正并重新输出完整代码。"
                    continue # 重试

                # 确保目录存在
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                generated_list.append(filepath)
                return # 成功退出
                
            except Exception as e:
                print(f"代码生成失败 [{filepath}]: {e}")
                if attempt == MAX_RETRIES - 1:
                    break # 达到最大重试次数
