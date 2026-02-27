from typing import List, Dict, Any
import logging
import json
from agents.base_agent import BaseAgent

from config import DEV_MODEL

logger = logging.getLogger(__name__)


class DevPlanGeneratorAgent(BaseAgent):
    def __init__(self, name: str = "开发计划生成专家", model_config_name: str = "dev_plan_generator"):
        super().__init__(name=name, model_config_name=model_config_name, model_name=DEV_MODEL)

    async def generate(self, work_packages: List[Dict[str, Any]], requirements: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        if not getattr(self, "model", None):
            return await self.generate_offline(work_packages)

        # 分批生成，每批 5 个
        CHUNK_SIZE = 5
        chunks = [work_packages[i:i + CHUNK_SIZE] for i in range(0, len(work_packages), CHUNK_SIZE)]
        
        all_plans = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"[{self.name}] 正在生成开发计划分块 {i+1}/{len(chunks)}...")
            try:
                chunk_plans = await self._generate_chunk(chunk, requirements)
                all_plans.extend(chunk_plans)
            except Exception as e:
                logger.error(f"[{self.name}] 分块 {i+1} 生成失败: {e}")
                # 失败则使用离线降级
                offline_plans = await self.generate_offline(chunk)
                all_plans.extend(offline_plans)
        
        logger.info(f"[{self.name}] 生成开发计划总数: {len(all_plans)}")
        return all_plans

    async def _generate_chunk(self, chunk: List[Dict[str, Any]], requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        # 使用 LLM 生成更详细的计划 (Markdown 模式)
        prompt = f"""
        作为开发计划生成专家，请根据以下工作包列表，生成详细的开发计划。
        
        【项目需求摘要】
        {json.dumps(requirements, ensure_ascii=False, indent=2)[:500] if requirements else "无额外需求"}

        【工作包列表 (本批次)】
        {json.dumps(chunk, ensure_ascii=False, indent=2)}
        
        请为每个工作包生成详细任务，并严格遵循以下规则：
        
        1. **基础设施包 (tags: infrastructure)**: 包含 Dockerfile, CI/CD, 公共库。
        2. **数据库包 (tags: db)**: 包含 Schema, Migration (无单元测试)。
        3. **API/后端包 (tags: api/component)**: 包含 接口编码, 单元测试, API文档。
        4. **前端包 (tags: frontend)**: 包含 组件编码, UI测试。
        5. **质量/测试/交付包**: 包含相应的验收和验证任务。
        
        【输出要求】
        请返回 **Markdown 列表** 格式。每个工作包一项，格式如下：
        
        ## <package_id>
        - tasks:
          - <task1>
          - <task2>
        - estimate_points: <int>
        - risk_level: <str>
        - risk_reason: <str>
        - acceptance_criteria:
          - <criteria1>
          - <criteria2>
        
        请确保包含所有工作包。
        """
        
        # 使用带重试机制的调用
        response = await self.call_llm_with_retry([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        
        # 解析 Markdown
        plans = self._extract_markdown(content, chunk)
        
        if not plans:
            raise ValueError("生成的计划为空或解析失败")

        return plans

    def _extract_markdown(self, content: str, work_packages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取并解析 Markdown 列表"""
        plans = []
        current_plan = {}
        
        # 预处理：按行分割
        lines = content.split('\n')
        
        import re
        package_ids = set(p['id'] for p in work_packages)
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # 匹配包 ID 标题 (## WP-001)
            header_match = re.match(r'^##\s*(WP-[\w-]+)', line)
            if header_match:
                # 保存上一个
                if current_plan and "package_id" in current_plan:
                    plans.append(current_plan)
                
                pkg_id = header_match.group(1)
                if pkg_id in package_ids:
                    current_plan = {"package_id": pkg_id}
                else:
                    current_plan = {} # 忽略未知ID
                continue
            
            if not current_plan: continue
            
            # 解析属性
            if line.startswith("- tasks:"):
                current_plan["tasks"] = []
            elif line.startswith("- acceptance_criteria:"):
                current_plan["acceptance_criteria"] = []
            elif line.startswith("- estimate_points:"):
                val = line.split(":", 1)[1].strip()
                current_plan["estimate_points"] = int(val) if val.isdigit() else 1
            elif line.startswith("- risk_level:"):
                current_plan["risk_level"] = line.split(":", 1)[1].strip()
            elif line.startswith("- risk_reason:"):
                current_plan["risk_reason"] = line.split(":", 1)[1].strip()
            
            # 解析列表项
            elif line.startswith("- ") or line.startswith("* "):
                item = line[2:].strip()
                # 确定归属
                # 简单起见，如果当前没有在 tasks 或 criteria 块中，忽略
                # 但 Markdown 解析比较麻烦，我们用更鲁棒的方式：
                # 假设任务列表在 estimate 之前，criteria 在最后
                # 或者我们用更简单的正则提取块
                pass 
        
        # 上述逐行解析太脆弱，改用正则块提取
        plans = []
        blocks = re.split(r'^##\s+', content, flags=re.MULTILINE)
        
        for block in blocks:
            if not block.strip(): continue
            
            lines = block.strip().split('\n')
            pkg_id_match = re.match(r'(WP-[\w-]+)', lines[0])
            if not pkg_id_match: continue
            
            pkg_id = pkg_id_match.group(1)
            if pkg_id not in package_ids: continue
            
            plan = {"package_id": pkg_id}
            
            # 提取字段
            # Tasks
            tasks_match = re.search(r'- tasks:\s*((?:  - .+\n?)+)', block)
            if tasks_match:
                tasks_raw = tasks_match.group(1)
                plan["tasks"] = [t.strip()[2:].strip() for t in tasks_raw.strip().split('\n') if t.strip().startswith("- ")]
            
            # Acceptance Criteria
            ac_match = re.search(r'- acceptance_criteria:\s*((?:  - .+\n?)+)', block)
            if ac_match:
                ac_raw = ac_match.group(1)
                plan["acceptance_criteria"] = [t.strip()[2:].strip() for t in ac_raw.strip().split('\n') if t.strip().startswith("- ")]
            
            # Others
            ep_match = re.search(r'- estimate_points:\s*(\d+)', block)
            if ep_match: plan["estimate_points"] = int(ep_match.group(1))
            
            rl_match = re.search(r'- risk_level:\s*(.+)', block)
            if rl_match: plan["risk_level"] = rl_match.group(1).strip()
            
            rr_match = re.search(r'- risk_reason:\s*(.+)', block)
            if rr_match: plan["risk_reason"] = rr_match.group(1).strip()
            
            # 默认值填充
            if "tasks" not in plan: plan["tasks"] = ["任务详情生成失败"]
            if "estimate_points" not in plan: plan["estimate_points"] = 1
            
            plans.append(plan)
            
        return plans



    async def generate_offline(self, work_packages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        plans: List[Dict[str, Any]] = []
        for p in work_packages:
            tags = p.get("tags", [])
            tasks = []

            if "infrastructure" in tags:
                tasks = [
                    "初始化仓库与目录结构",
                    "补齐基础配置与环境变量样例",
                    "搭建最小可运行框架",
                    "校验基础启动与构建"
                ]
            elif "testing" in tags:
                tasks = [
                    "梳理测试范围与覆盖目标",
                    "实现测试脚本",
                    "本地执行并修复失败项",
                    "输出测试报告"
                ]
            elif "delivery" in tags or "acceptance" in tags:
                tasks = [
                    "准备交付环境",
                    "执行并支持 UAT",
                    "整理并移交文档",
                    "完成验收确认"
                ]
            elif "quality" in tags:
                tasks = [
                    "定义质量门禁与验收标准",
                    "梳理风险清单与收敛动作",
                    "组织回归验证",
                    "输出质量收敛结论"
                ]
            elif "db" in tags:
                tasks = [
                    "设计表结构与字段约束",
                    "编写建表与索引 SQL",
                    "编写迁移脚本",
                    "执行迁移测试"
                ]
            elif "frontend" in tags:
                tasks = [
                    "确定页面与组件结构",
                    "实现核心组件",
                    "对接接口并完成联调",
                    "编写 UI/交互测试"
                ]
            else:
                tasks = [
                    "梳理接口与数据契约",
                    "实现核心逻辑",
                    "自测与边界用例校验",
                    "编写单元测试",
                    "完善接口文档"
                ]

            plan = {
                "package_id": p["id"],
                "status_machine": ["planned", "in_progress", "review", "testing", "done"],
                "acceptance_criteria": p.get("acceptance_criteria", ["功能达成", "测试通过", "无阻断风险"]),
                "risk": "low",
                "dependencies": p.get("depends_on", []),
                "estimate": {
                    "points": max(1, len(p.get("software_unit_ids", [])))
                },
                "tasks": tasks
            }
            plans.append(plan)
        return plans

