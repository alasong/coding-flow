from typing import Dict, Any
from agents.base_agent import BaseAgent
from config import DEV_MODEL

class DevRunVerifierAgent(BaseAgent):
    def __init__(self, name: str = "开发运行验证专家", model_config_name: str = "dev_run_verifier"):
        super().__init__(name=name, model_config_name=model_config_name, model_name=None  # 使用平台默认模型)

    async def verify(self, output_dir: str) -> Dict[str, Any]:
        import os
        import subprocess
        
        base = os.path.join(output_dir, "project_code")
        
        # 1. 运行 Pytest
        try:
            # 设置环境变量，将当前目录加入 PYTHONPATH，确保能导入 app 模块
            env = os.environ.copy()
            env["PYTHONPATH"] = base + os.pathsep + env.get("PYTHONPATH", "")
            
            # 运行所有测试，并生成简要报告
            result = subprocess.run(
                ["pytest", "--tb=short", "-q"],
                cwd=base,
                env=env,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            test_success = result.returncode == 0
            test_output = result.stdout + result.stderr
            
        except Exception as e:
            test_success = False
            test_output = f"测试执行异常: {str(e)}"
            
        # 2. 使用 LLM 分析测试结果 (如果失败)
        analysis = ""
        if not test_success:
             # 安全处理 test_output，避免 None
             log_content = test_output if test_output else "无日志输出"
             
             prompt = f"""
             测试运行失败，请分析以下 Pytest 输出日志，并给出修复建议。
             
             【测试日志】
             {log_content[:2000]}
             
             请重点关注 ImportError 和 ModuleNotFoundError。
             如果发现是导入错误，请明确指出是哪个模块缺失或路径错误。
             请给出具体的修复代码建议。
             """
             try:
                 response = await self.model([{"role": "user", "content": prompt}])
                 analysis = await self._process_model_response(response)
             except Exception as e:
                 print(f"智能分析失败: {e}")
                 analysis = "无法进行智能分析"

        # 3. 生成验证报告
        report_path = os.path.join(base, "verify_report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# 自动化验证报告\n\n")
            f.write(f"**测试状态**: {'✅ 通过' if test_success else '❌ 失败'}\n\n")
            f.write("## 测试输出\n")
            f.write(f"```\n{test_output}\n```\n")
            if analysis:
                f.write("\n## 故障分析\n")
                f.write(analysis)
            
        return {
            "build": True, # 暂时假设无需编译
            "tests": test_success,
            "output": test_output
        }
