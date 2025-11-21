#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主工作流协调器
统一管理和协调所有工作流，包括需求分析工作流和架构设计工作流
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from abc import abstractmethod

from workflow.base_workflow import BaseWorkflow
from workflow.requirement_workflow import RequirementAnalysisWorkflow
from workflow.architecture_workflow import ArchitectureDesignWorkflow
from workflow.development_workflow import ProjectDevelopmentWorkflow
from workflow.development_execution_workflow import DevelopmentExecutionWorkflow
from config import MASTER_WORKFLOW_CONFIG, OUTPUT_DIR
from utils.common import get_project_slug
import logging

logger = logging.getLogger(__name__)

class MasterWorkflow(BaseWorkflow):
    """主工作流协调器"""
    
    def __init__(self):
        super().__init__("主工作流协调器")
        self.requirement_workflow = None
        self.architecture_workflow = None
        self.workflow_history = []
        self.context = {}
        
        # 根据配置初始化子工作流
        if MASTER_WORKFLOW_CONFIG.get("enable_requirement_workflow", True):
            self.requirement_workflow = RequirementAnalysisWorkflow()
            logger.info("需求分析工作流已启用")
        
        if MASTER_WORKFLOW_CONFIG.get("enable_architecture_workflow", True):
            self.architecture_workflow = ArchitectureDesignWorkflow()
            logger.info("架构设计工作流已启用")

        if MASTER_WORKFLOW_CONFIG.get("enable_development_workflow", True):
            self.development_workflow = ProjectDevelopmentWorkflow()
            logger.info("项目分解工作流已启用")
        else:
            self.development_workflow = None
        if MASTER_WORKFLOW_CONFIG.get("enable_development_execution_workflow", True):
            self.development_execution_workflow = DevelopmentExecutionWorkflow()
            logger.info("项目开发工作流已启用")
        else:
            self.development_execution_workflow = None
    
    def _establish_requirement_architecture_mapping(self) -> None:
        """建立需求与架构的关联映射"""
        try:
            requirement_analysis = self.context.get("requirement_analysis", {})
            architecture_design = self.context.get("architecture_design", {})
            
            # 从需求分析结果中获取需求条目
            requirement_entries = []
            if "results" in requirement_analysis and "requirement_items" in requirement_analysis["results"]:
                # 新的需求分析工作流返回结构
                requirement_entries = requirement_analysis["results"]["requirement_items"].get("requirement_entries", [])
            elif "requirement_entries" in requirement_analysis:
                # 兼容旧版本结构
                requirement_entries = requirement_analysis.get("requirement_entries", [])
            
            architecture_result = architecture_design.get("final_result", {})
            
            # 创建关联映射
            mapping = {
                "requirement_architecture_mapping": {
                    "total_requirements": len(requirement_entries),
                    "mapping_created_at": datetime.now().isoformat(),
                    "mappings": []
                }
            }
            
            # 为每个需求条目建立与架构组件的映射
            for requirement in requirement_entries:
                req_id = requirement.get("id", "")
                req_type = requirement.get("type", "")
                req_description = requirement.get("description", "")
                
                # 从架构结果中查找相关组件
                related_components = self._find_related_architecture_components(requirement, architecture_result)
                
                mapping["requirement_architecture_mapping"]["mappings"].append({
                    "requirement_id": req_id,
                    "requirement_type": req_type,
                    "requirement_description": req_description,
                    "related_components": related_components,
                    "mapping_score": len(related_components) * 20,  # 简单的评分机制
                    "coverage_status": "已覆盖" if related_components else "未覆盖"
                })
            
            # 计算总体覆盖率
            total_requirements = len(requirement_entries)
            covered_requirements = len([m for m in mapping["requirement_architecture_mapping"]["mappings"] if m["coverage_status"] == "已覆盖"])
            mapping["requirement_architecture_mapping"]["overall_coverage"] = {
                "total_requirements": total_requirements,
                "covered_requirements": covered_requirements,
                "coverage_percentage": (covered_requirements / total_requirements * 100) if total_requirements > 0 else 0
            }
            
            # 存储映射到上下文
            self.context["requirement_architecture_mapping"] = mapping["requirement_architecture_mapping"]
            
            logger.info(f"已建立需求与架构的关联映射，覆盖率: {mapping['requirement_architecture_mapping']['overall_coverage']['coverage_percentage']:.1f}%")
            
        except Exception as e:
            logger.error(f"建立需求与架构映射失败: {str(e)}")
            self.context["requirement_architecture_mapping_error"] = str(e)
    
    def _find_related_architecture_components(self, requirement: Dict[str, Any], architecture_result: Dict[str, Any]) -> List[str]:
        """查找与需求相关的架构组件"""
        related_components = []
        requirement_text = requirement.get("description", "").lower()
        req_type = requirement.get("type", "")
        req_id = requirement.get("id", "")
        
        # 从架构设计结果中查找相关组件
        # 首先尝试从 architecture_analysis 步骤结果中获取
        steps = architecture_result.get("steps", {})
        architecture_analysis = steps.get("architecture_analysis", {})
        
        # 获取系统架构数据
        system_architecture = architecture_analysis.get("result", {}).get("system_architecture", {})
        components = system_architecture.get("system_components", [])
        
        # 如果没有找到，尝试其他可能的路径
        if not components:
            # 尝试直接从 architecture_design 获取
            architecture_design = architecture_result.get("architecture_design", {})
            if "system_architecture" in architecture_design:
                components = architecture_design["system_architecture"].get("system_components", [])
            elif "components" in architecture_design:
                components = architecture_design["components"]
        
        # 为不同类型的需求使用不同的匹配策略
        if req_type == "functional":
            # 功能性需求 - 基于业务关键词匹配
            keywords = self._extract_business_keywords(requirement_text)
        else:
            # 非功能性需求 - 基于技术关键词匹配
            keywords = self._extract_technical_keywords(requirement_text)
        
        for component in components:
            component_name = component.get("name", "").lower()
            component_description = component.get("description", "").lower()
            component_text = f"{component_name} {component_description}"
            
            # 计算匹配分数
            match_score = 0
            for keyword in keywords:
                if keyword in component_text:
                    match_score += 1
            
            # 特殊规则：如果需求ID包含特定前缀，增加相关组件的匹配概率
            if req_id.startswith("FR-") and "service" in component_name:
                match_score += 0.5  # 功能性需求倾向于匹配服务组件
            elif req_id.startswith("NFR-") and any(term in component_name for term in ["security", "monitor", "cache", "gateway"]):
                match_score += 0.5  # 非功能性需求倾向于匹配基础设施组件
            
            # 如果匹配分数大于0，则认为相关
            if match_score > 0:
                related_components.append(component.get("name", ""))
        
        return related_components
    
    def _extract_business_keywords(self, text: str) -> List[str]:
        """提取业务关键词"""
        # 中文业务词汇
        business_terms = [
            '用户', '注册', '登录', '订单', '产品', '商品', '支付', '购物车', '库存', '分类',
            '搜索', '推荐', '评论', '评价', '收藏', '地址', '配送', '物流', '退款', '售后',
            '权限', '角色', '管理', '系统', '服务', '接口', '数据', '安全', '认证', '授权',
            '邮箱', '手机', '短信', '验证码', '密码', '头像', '昵称', '个人信息', '账户',
            '购买', '下单', '付款', '发货', '收货', '退货', '换货', '维修', '投诉', '咨询',
            '浏览', '查看', '编辑', '删除', '添加', '更新', '查询', '筛选', '排序', '分页'
        ]
        
        keywords = []
        text_lower = text.lower()
        
        # 匹配业务词汇
        for term in business_terms:
            if term in text_lower:
                keywords.append(term)
        
        # 提取英文关键词（如用户提到的特定技术或概念）
        import re
        english_words = re.findall(r'\b[a-zA-Z]+\b', text_lower)
        for word in english_words:
            if len(word) > 2 and word not in ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can']:
                keywords.append(word)
        
        return keywords[:10]  # 限制关键词数量
    
    def _extract_technical_keywords(self, text: str) -> List[str]:
        """提取技术关键词"""
        # 技术相关词汇
        technical_terms = [
            '性能', '安全', '可靠', '可用', '扩展', '伸缩', '并发', '响应', '延迟', '吞吐',
            '容量', '存储', '内存', 'CPU', '网络', '带宽', '延迟', '缓存', '数据库', '备份',
            '恢复', '容灾', '监控', '告警', '日志', '审计', '加密', '认证', '授权', '防火墙',
            '负载', '均衡', '集群', '分布', '微服务', '容器', '虚拟', '云', '弹性', '自动',
            '高可用', '容错', '冗余', '备份', '监控', '运维', '部署', '升级', '维护', '配置'
        ]
        
        keywords = []
        text_lower = text.lower()
        
        # 匹配技术词汇
        for term in technical_terms:
            if term in text_lower:
                keywords.append(term)
        
        return keywords[:8]  # 限制关键词数量，避免过度匹配

    def get_workflow_info(self) -> Dict[str, Any]:
        """获取工作流信息"""
        return {
            "name": self.name,
            "description": "统一管理和协调所有工作流的主协调器",
            "enabled_workflows": {
                "requirement_analysis": self.requirement_workflow is not None,
                "architecture_design": self.architecture_workflow is not None
            },
            "configuration": MASTER_WORKFLOW_CONFIG,
            "total_runs": len(self.workflow_history),
            "context_keys": list(self.context.keys()),
            "mapping_established": "requirement_architecture_mapping" in self.context
        }
    
    async def _execute_step(self, step_name: str, input_data: Any, **kwargs) -> Dict[str, Any]:
        """执行单个步骤"""
        logger.info(f"执行步骤: {step_name}")
        
        step_start_time = datetime.now()
        
        try:
            if step_name == "requirement_analysis":
                if not self.requirement_workflow:
                    raise ValueError("需求分析工作流未启用")
                
                # 执行需求分析工作流
                result = await self.requirement_workflow.run(input_data, **kwargs)
                
                # 将需求分析结果存储到上下文
                self.context["requirement_analysis"] = result
                self.context["core_requirements"] = result.get("core_requirements", {})
                
                logger.info("需求分析步骤完成")
                return result
            
            elif step_name == "architecture_design":
                if not self.architecture_workflow:
                    raise ValueError("架构设计工作流未启用")
                
                # 准备架构设计的输入数据
                if "requirement_analysis" in self.context:
                    # 使用完整的需求分析结果作为输入，包含需求条目
                    requirement_analysis = self.context["requirement_analysis"]
                    
                    # 从需求分析结果中获取需求条目
                    if "results" in requirement_analysis and "requirement_items" in requirement_analysis["results"]:
                        # 新的需求分析工作流返回结构
                        requirement_entries = requirement_analysis["results"]["requirement_items"].get("requirement_entries", [])
                        architecture_input = requirement_analysis["results"]["requirement_items"]
                    elif "requirement_entries" in requirement_analysis:
                        # 兼容旧版本结构
                        requirement_entries = requirement_analysis.get("requirement_entries", [])
                        architecture_input = requirement_analysis
                    else:
                        # 默认使用完整结果
                        requirement_entries = []
                        architecture_input = requirement_analysis
                    
                    logger.info(f"使用需求分析结果作为架构设计输入，包含 {len(requirement_entries)} 个需求条目")
                elif "core_requirements" in self.context:
                    # 兼容旧版本的核心需求
                    architecture_input = self.context["core_requirements"]
                    logger.info("使用核心需求作为架构设计输入")
                else:
                    # 直接使用输入数据
                    architecture_input = input_data
                    logger.info("使用原始输入数据作为架构设计输入")
                
                # 执行架构设计工作流
                result = await self.architecture_workflow.run(architecture_input, **kwargs)
                
                # 将架构设计结果存储到上下文
                self.context["architecture_design"] = result
                
                # 建立需求与架构的关联映射
                if "requirement_analysis" in self.context:
                    self._establish_requirement_architecture_mapping()
                
                logger.info("架构设计步骤完成")
                return result
            elif step_name == "decomposition":
                if not getattr(self, "development_workflow", None):
                    raise ValueError("项目分解工作流未启用")
                arch_ctx = self.context.get("architecture_design", {})
                arch_final = arch_ctx.get("final_result", {})
                architecture_analysis = arch_final.get("architecture_design", {})
                dev_result = await self.development_workflow.execute(architecture_analysis, output_dir=OUTPUT_DIR)
                self.context["decomposition"] = dev_result
                logger.info("项目分解步骤完成")
                return dev_result
            elif step_name == "development_execution":
                if not getattr(self, "development_execution_workflow", None):
                    raise ValueError("项目开发工作流未启用")
                decomp_ctx = self.context.get("decomposition", {})
                devexec_result = await self.development_execution_workflow.execute(decomp_ctx, output_dir=f"{OUTPUT_DIR}/development_execution")
                self.context["development_execution"] = devexec_result
                logger.info("项目开发步骤完成")
                return devexec_result
            
            else:
                raise ValueError(f"未知步骤: {step_name}")
        
        except Exception as e:
            logger.error(f"步骤 {step_name} 执行失败: {e}")
            raise
        
        finally:
            step_duration = (datetime.now() - step_start_time).total_seconds()
            self.workflow_history.append({
                "step": step_name,
                "timestamp": step_start_time.isoformat(),
                "duration": step_duration,
                "status": "completed" if 'result' in locals() else "failed"
            })
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流 - 实现抽象方法"""
        return asyncio.run(self.run(input_data.get("content", ""), input_data.get("mode", "sequential")))
    
    def get_workflow_steps(self) -> List[Dict[str, Any]]:
        """获取工作流步骤 - 实现抽象方法"""
        steps = []
        if self.requirement_workflow:
            steps.append({"name": "requirement_analysis", "description": "需求分析"})
        if self.architecture_workflow:
            steps.append({"name": "architecture_design", "description": "架构设计"})
        if getattr(self, "development_workflow", None):
            steps.append({"name": "decomposition", "description": "项目分解"})
        if getattr(self, "development_execution_workflow", None):
            steps.append({"name": "development_execution", "description": "项目开发"})
        return steps
    
    async def run(self, input_data: str, workflow_mode: str = "sequential", **kwargs) -> Dict[str, Any]:
        """
        运行主工作流
        
        Args:
            input_data: 输入数据
            workflow_mode: 工作流模式 (sequential, parallel, requirement_only, architecture_only)
            **kwargs: 其他参数
        
        Returns:
            工作流结果
        """
        logger.info(f"开始执行主工作流，模式: {workflow_mode}")
        start_time = datetime.now()
        
        try:
            # 验证输入
            if not input_data or not input_data.strip():
                raise ValueError("输入数据不能为空")
            import os
            project_slug = get_project_slug(input_data)
            project_output_dir = os.path.join(OUTPUT_DIR, project_slug)
            os.makedirs(project_output_dir, exist_ok=True)
            
            # 初始化结果容器
            results = {
                "workflow_info": {
                    "name": self.name,
                    "mode": workflow_mode,
                    "start_time": start_time.isoformat(),
                    "status": "running"
                },
                "context": {},
                "results": {}
            }
            
            # 根据模式执行工作流
            if workflow_mode == "sequential":
                # 顺序执行所有启用的工作流
                if self.requirement_workflow:
                    logger.info("开始执行需求分析工作流")
                    requirement_result = await self.requirement_workflow.run(input_data, output_dir=project_output_dir)
                    # 将需求分析结果存储到上下文
                    self.context["requirement_analysis"] = requirement_result
                    self.context["core_requirements"] = requirement_result.get("core_requirements", {})
                    results["results"]["requirement_analysis"] = requirement_result
                
                if self.architecture_workflow:
                    logger.info("开始执行架构设计工作流")
                    req_result = self.context.get("requirement_analysis", {})
                    if "results" in req_result and "requirement_items" in req_result["results"]:
                        architecture_input = req_result["results"]["requirement_items"]
                    else:
                        architecture_input = req_result
                    architecture_result = await self.architecture_workflow.run(architecture_input, output_dir=project_output_dir)
                    self.context["architecture_design"] = architecture_result
                    results["results"]["architecture_design"] = architecture_result
                if getattr(self, "development_workflow", None):
                    logger.info("开始执行项目分解工作流")
                    arch_ctx = self.context.get("architecture_design", {})
                    arch_final = arch_ctx.get("final_result", {})
                    architecture_analysis = arch_final.get("architecture_design", {})
                    development_result = await self.development_workflow.execute(architecture_analysis, output_dir=os.path.join(project_output_dir, "decomposition"))
                    self.context["decomposition"] = development_result
                    results["results"]["decomposition"] = development_result
                if getattr(self, "development_execution_workflow", None):
                    logger.info("开始执行项目开发工作流")
                    devexec_result = await self.development_execution_workflow.execute(
                        self.context.get("decomposition", {}),
                        requirements=self.context.get("requirement_analysis", {}),
                        architecture=self.context.get("architecture_design", {}),
                        output_dir=os.path.join(project_output_dir, "development_execution")
                    )
                    self.context["development_execution"] = devexec_result
                    results["results"]["development_execution"] = devexec_result
            
            elif workflow_mode == "parallel":
                # 并行执行工作流
                tasks = []
                
                if self.requirement_workflow:
                    tasks.append(self._execute_step("requirement_analysis", input_data, **kwargs))
                
                if self.architecture_workflow:
                    tasks.append(self._execute_step("architecture_design", input_data, **kwargs))
                
                if tasks:
                    # 并行执行所有任务
                    parallel_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # 处理结果
                    if self.requirement_workflow and self.architecture_workflow:
                        results["results"]["requirement_analysis"] = parallel_results[0]
                        results["results"]["architecture_design"] = parallel_results[1]
                    elif self.requirement_workflow:
                        results["results"]["requirement_analysis"] = parallel_results[0]
                    elif self.architecture_workflow:
                        results["results"]["architecture_design"] = parallel_results[0]
            
            elif workflow_mode == "requirement_only":
                # 仅执行需求分析
                if self.requirement_workflow:
                    requirement_result = await self._execute_step("requirement_analysis", input_data, **kwargs)
                    results["results"]["requirement_analysis"] = requirement_result
                else:
                    logger.warning("需求分析工作流未启用")
            
            elif workflow_mode == "architecture_only":
                # 仅执行架构设计
                if self.architecture_workflow:
                    architecture_result = await self._execute_step("architecture_design", input_data, **kwargs)
                    results["results"]["architecture_design"] = architecture_result
                else:
                    logger.warning("架构设计工作流未启用")
            
            else:
                raise ValueError(f"不支持的工作流模式: {workflow_mode}")
            
            # 计算总耗时
            total_duration = (datetime.now() - start_time).total_seconds()
            
            # 更新工作流信息
            results["workflow_info"].update({
                "end_time": datetime.now().isoformat(),
                "total_duration": total_duration,
                "status": "completed",
                "steps_executed": len(results["results"]),
                "context_summary": {
                    "has_requirements": "core_requirements" in self.context or "requirement_analysis" in self.context,
                    "has_architecture": "architecture_design" in self.context,
                    "has_mapping": "requirement_architecture_mapping" in self.context,
                    "context_keys": list(self.context.keys()),
                    "requirement_entries_count": len(self.context.get("requirement_analysis", {}).get("requirement_entries", [])),
                    "mapping_coverage": self.context.get("requirement_architecture_mapping", {}).get("overall_coverage", {}).get("coverage_percentage", 0)
                }
            })
            
            # 添加上下文信息
            results["context"] = self.context
            
            logger.info(f"主工作流执行完成，总耗时: {total_duration:.2f} 秒")
            
            # 保存结果
            if MASTER_WORKFLOW_CONFIG.get("save_intermediate_results", True):
                await self._save_results(results)
            
            return results
            
        except Exception as e:
            logger.error(f"主工作流执行失败: {e}")
            
            # 记录错误信息
            error_info = {
                "workflow_info": {
                    "name": self.name,
                    "mode": workflow_mode,
                    "start_time": start_time.isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "status": "failed",
                    "error": str(e)
                },
                "error_details": {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "workflow_history": self.workflow_history[-5:]  # 最近5条历史记录
                }
            }
            
            # 保存错误信息
            if MASTER_WORKFLOW_CONFIG.get("save_intermediate_results", True):
                await self._save_results(error_info, is_error=True)
            
            raise
    
    async def _save_results(self, results: Dict[str, Any], is_error: bool = False):
        """保存工作流结果"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if is_error:
                # 保存错误信息
                error_file = Path(OUTPUT_DIR) / f"master_workflow_error_{timestamp}.json"
                with open(error_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                logger.info(f"错误信息已保存到: {error_file}")
            else:
                # 保存完整结果
                json_file = Path(OUTPUT_DIR) / f"master_workflow_result_{timestamp}.json"
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                logger.info(f"工作流结果已保存到: {json_file}")
                
                # 生成Markdown格式的摘要
                md_file = Path(OUTPUT_DIR) / f"master_workflow_summary_{timestamp}.md"
                self._generate_markdown_summary(results, md_file)
                
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
    
    def _generate_markdown_summary(self, results: Dict[str, Any], md_file: Path):
        """生成Markdown格式的摘要"""
        try:
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write("# 主工作流执行结果摘要\n\n")
                
                # 工作流信息
                workflow_info = results.get("workflow_info", {})
                f.write(f"**执行模式**: {workflow_info.get('mode', 'unknown')}\n")
                f.write(f"**开始时间**: {workflow_info.get('start_time', 'unknown')}\n")
                f.write(f"**结束时间**: {workflow_info.get('end_time', 'unknown')}\n")
                f.write(f"**总耗时**: {workflow_info.get('total_duration', 0):.2f} 秒\n")
                f.write(f"**执行状态**: {workflow_info.get('status', 'unknown')}\n")
                f.write(f"**执行步骤**: {workflow_info.get('steps_executed', 0)}\n\n")
                
                # 上下文摘要
                context_summary = workflow_info.get("context_summary", {})
                f.write("## 上下文摘要\n")
                f.write(f"- 包含需求信息: {'是' if context_summary.get('has_requirements') else '否'}\n")
                f.write(f"- 包含架构信息: {'是' if context_summary.get('has_architecture') else '否'}\n")
                f.write(f"- 上下文键值: {', '.join(context_summary.get('context_keys', []))}\n\n")
                
                # 工作流结果摘要
                workflow_results = results.get("results", {})
                
                if "requirement_analysis" in workflow_results:
                    f.write("## 需求分析结果摘要\n")
                    req_result = workflow_results["requirement_analysis"]
                    req_info = req_result.get("workflow_info", {})
                    f.write(f"- 状态: {req_info.get('status', 'unknown')}\n")
                    f.write(f"- 耗时: {req_info.get('total_duration', 0):.2f} 秒\n")
                    f.write(f"- 核心需求数量: {len(req_result.get('core_requirements', {}))}\n\n")
                
                if "architecture_design" in workflow_results:
                    f.write("## 架构设计结果摘要\n")
                    arch_result = workflow_results["architecture_design"]
                    arch_info = arch_result.get("workflow_info", {})
                    f.write(f"- 状态: {arch_info.get('status', 'unknown')}\n")
                    f.write(f"- 耗时: {arch_info.get('total_duration', 0):.2f} 秒\n")
                    
                    # 架构验证评分
                    validation = arch_result.get("architecture_validation", {})
                    if validation:
                        f.write(f"- 总体评分: {validation.get('overall_score', 0)}/10\n")
                    f.write("\n")
                
                f.write("## 详细结果\n")
                f.write("完整结果请查看对应的JSON文件。\n")
                
            logger.info(f"Markdown摘要已保存到: {md_file}")
            
        except Exception as e:
            logger.error(f"生成Markdown摘要失败: {e}")
    
    def get_context(self) -> Dict[str, Any]:
        """获取当前上下文"""
        return self.context.copy()
    
    def clear_context(self):
        """清空上下文"""
        self.context.clear()
        logger.info("上下文已清空")
    
    def get_workflow_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取工作流历史"""
        if limit:
            return self.workflow_history[-limit:]
        return self.workflow_history.copy()

# 使用示例和测试函数
async def test_master_workflow():
    """测试主工作流协调器"""
    logger.info("开始测试主工作流协调器")
    
    # 创建主工作流实例
    master_workflow = MasterWorkflow()
    
    # 测试不同的工作流模式
    test_input = """
    # 在线学习平台需求
    
    ## 功能需求
    - 用户注册、登录、个人资料管理
    - 课程发布、管理、搜索
    - 视频播放、进度跟踪
    - 作业提交、批改
    - 在线考试、成绩管理
    - 讨论区、消息通知
    
    ## 非功能需求
    - 支持10万并发用户
    - 视频播放流畅无卡顿
    - 数据安全可靠
    - 界面友好易用
    """
    
    # 测试顺序模式
    logger.info("\n=== 测试顺序模式 ===")
    try:
        sequential_result = await master_workflow.run(test_input, workflow_mode="sequential")
        logger.info("顺序模式测试完成")
        logger.info(f"总耗时: {sequential_result['workflow_info']['total_duration']:.2f} 秒")
    except Exception as e:
        logger.error(f"顺序模式测试失败: {e}")
    
    # 测试仅需求分析模式
    logger.info("\n=== 测试仅需求分析模式 ===")
    try:
        master_workflow.clear_context()  # 清空上下文
        requirement_only_result = await master_workflow.run(test_input, workflow_mode="requirement_only")
        logger.info("仅需求分析模式测试完成")
    except Exception as e:
        logger.error(f"仅需求分析模式测试失败: {e}")
    
    # 测试仅架构设计模式
    logger.info("\n=== 测试仅架构设计模式 ===")
    try:
        master_workflow.clear_context()  # 清空上下文
        architecture_only_result = await master_workflow.run(test_input, workflow_mode="architecture_only")
        logger.info("仅架构设计模式测试完成")
    except Exception as e:
        logger.error(f"仅架构设计模式测试失败: {e}")
    
    logger.info("主工作流协调器测试完成")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_master_workflow())
