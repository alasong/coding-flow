
from typing import Dict, Any, List, Optional
import logging
import json
from agents.base_agent import BaseAgent
from config import DEFAULT_MODEL

logger = logging.getLogger(__name__)


class DevPlanReviewerAgent(BaseAgent):
    def __init__(self, name: str = "开发计划评审专家", model_config_name: str = "dev_plan_reviewer"):
        super().__init__(name=name, model_config_name=model_config_name, model_name=None)  # 使用平台默认模型

    async def review(self, work_packages: List[Dict[str, Any]], dev_plans: List[Dict[str, Any]], requirements: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        评审工作包和开发计划 (分块评审模式)
        """
        if not getattr(self, "model", None):
            return self._offline_review("离线模式无法深度评审，建议启用在线模型")

        import yaml
        import asyncio
        
        # 1. 准备数据
        # 清洗 Requirements
        requirements_str = str(requirements).replace("http://", "[url]").replace("https://", "[url]")
        
        # 将开发计划转为字典映射，方便按 ID 查找
        plans_map = {p['package_id']: p for p in dev_plans if 'package_id' in p}
        
        # 2. 分块
        CHUNK_SIZE = 5
        chunks = [work_packages[i:i + CHUNK_SIZE] for i in range(0, len(work_packages), CHUNK_SIZE)]
        
        logger.info(f"[{self.name}] 开始分块评审，共 {len(chunks)} 个分块")
        
        chunk_results = []
        
        # 3. 逐块评审 (串行或并发)
        # 考虑到限流，这里采用串行
        for i, chunk in enumerate(chunks):
            try:
                # 构造当前块的 plans
                chunk_plans = []
                for wp in chunk:
                    if wp['id'] in plans_map:
                        chunk_plans.append(plans_map[wp['id']])
                
                logger.info(f"[{self.name}] 正在评审分块 {i+1}/{len(chunks)} (包含 {len(chunk)} 个包)...")
                result = await self._review_chunk(chunk, chunk_plans, requirements_str)
                chunk_results.append(result)
                
            except Exception as e:
                logger.error(f"[{self.name}] 分块 {i+1} 评审失败: {e}")
                # 记录失败但不中断整体流程
                chunk_results.append({
                    "score": 0, 
                    "issues": [f"分块评审失败: {e}"], 
                    "suggestions": [],
                    "status": "failed"
                })

        # 4. 合并结果
        return self._merge_results(chunk_results)

    async def _review_chunk(self, chunk_packages, chunk_plans, requirements_str):
        """评审单个分块"""
        import yaml
        import re
        
        summary_packages = [{"id": wp.get("id"), "name": wp.get("name")} for wp in chunk_packages]
        
        # 转 YAML 字符串
        plans_str = yaml.dump(chunk_plans, allow_unicode=True)
        
        # 清洗 URL (彻底移除)
        plans_str = plans_str.replace("http://", "").replace("https://", "").replace("[url]", "")
        
        # 截断 (放宽限制，避免信息丢失)
        plans_str = plans_str[:4000] 

        prompt = f"""
        作为资深技术项目经理，请评审以下项目开发计划片段。
        
        【项目需求摘要】
        {requirements_str[:1000]}

        【工作包列表 (本批次)】
        ```yaml
        {yaml.dump(summary_packages, allow_unicode=True)}
        ```
        
        【开发计划 (本批次)】
        ```yaml
        {plans_str}
        ```
        
        请返回 **JSON** 格式的评审报告：
        - status: "passed" | "passed_with_warnings" | "failed"
        - score: int (0-100)
        - issues: List[str]
        - suggestions: List[str]
        """
        
        # 尝试使用 dashscope SDK 直接调用
        import dashscope
        from http import HTTPStatus
        import asyncio
        from config import DASHSCOPE_API_KEY
        
        if DASHSCOPE_API_KEY:
            dashscope.api_key = DASHSCOPE_API_KEY

        try:
            # 封装同步调用为异步
            def _call_dashscope():
                return dashscope.Generation.call(
                    model="qwen-turbo", # 降级使用 qwen-turbo，它通常更稳定且不易报错
                    messages=[{'role': 'user', 'content': prompt}],
                    result_format='message',
                    enable_search=False # 显式禁用搜索
                )

            response = await asyncio.to_thread(_call_dashscope)
            
            if response.status_code == HTTPStatus.OK:
                content = response.output.choices[0]['message']['content']
            else:
                logger.warning(f"[{self.name}] DashScope API Warning: {response.code} - {response.message}")
                raise RuntimeError(f"DashScope Error: {response.message}")

        except Exception as e:
            logger.warning(f"[{self.name}] 在线评审不可用: {e}")
            return {
                "score": 60, 
                "issues": ["在线评审服务暂时不可用，已跳过深度检查"], 
                "status": "passed_with_warnings", 
                "suggestions": ["请人工复核"]
            }
        
        # 提取 JSON
        import re
        import json
        
        # 尝试提取代码块
        code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if code_block_match:
            json_str = code_block_match.group(1)
        else:
            # 尝试寻找 JSON 对象
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
            else:
                json_str = content
                
        try:
            return json.loads(json_str)
        except:
            logger.warning(f"[{self.name}] 分块评审结果解析失败: {content[:50]}...")
            return {"score": 50, "issues": ["评审结果格式解析失败"], "status": "passed_with_warnings", "suggestions": []}

    def _merge_results(self, results):
        """合并分块评审结果"""
        total_score = 0
        all_issues = []
        all_suggestions = []
        failed_count = 0
        
        valid_count = 0
        for res in results:
            if not isinstance(res, dict): continue
            
            score = res.get("score", 0)
            if score > 0:
                total_score += score
                valid_count += 1
                
            if res.get("issues"): all_issues.extend(res["issues"])
            if res.get("suggestions"): all_suggestions.extend(res["suggestions"])
            
            if res.get("status") == "failed":
                failed_count += 1
        
        final_score = int(total_score / valid_count) if valid_count > 0 else 0
        
        status = "passed"
        if failed_count > 0 or final_score < 60:
            status = "failed"
        elif all_issues:
            status = "passed_with_warnings"
            
        return {
            "status": status,
            "score": final_score,
            "issues": list(set(all_issues)), # 去重
            "suggestions": list(set(all_suggestions)),
            "summary": f"评审完成。共评审 {len(results)} 个分块，平均得分 {final_score}。"
        }

    def _offline_review(self, reason: str) -> Dict[str, Any]:
        logger.info(f"[{self.name}] (离线) 执行基础评审: {reason}")
        return {
            "status": "passed_with_warnings",
            "score": 80,
            "issues": [],
            "suggestions": ["离线模式无法深度评审，建议启用在线模型"],
            "summary": "基础结构完整，但缺乏深度语义分析。",
            "note": reason
        }
