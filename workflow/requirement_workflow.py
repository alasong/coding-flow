"""
需求分析工作流 - 使用AgentScope 1.0.7兼容版本
集成关键决策点组件，支持产品经理确认关键业务决策
"""

import logging
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Any

# 导入Agent类
from agents.requirement_collector import RequirementCollectorAgent
from agents.requirement_analyzer import RequirementAnalyzerAgent
from agents.requirement_validator import RequirementValidatorAgent
from agents.document_generator import DocumentGeneratorAgent

# 导入关键决策点组件
from agents.key_decision_point import (
    DecisionPointGenerator,
    DecisionConfirmUI,
    DecisionApplier,
    DecisionReportGenerator
)

# 配置日志
logger = logging.getLogger(__name__)

# Agent配置
AGENT_CONFIGS = {
    "requirement_collector": {
        "name": "需求收集Agent",
        "model_config_name": "requirement-collector"
    },
    "requirement_analyzer": {
        "name": "需求分析Agent", 
        "model_config_name": "requirement-analyzer"
    },
    "requirement_validator": {
        "name": "需求验证Agent",
        "model_config_name": "requirement-validator"
    },
    "document_generator": {
        "name": "文档生成Agent",
        "model_config_name": "document-generator"
    }
}

from workflow.base_workflow import BaseWorkflow

class RequirementAnalysisWorkflow(BaseWorkflow):
    """需求分析工作流 - 协调多个Agent完成需求分析任务"""
    
    def __init__(self):
        """初始化工作流"""
        super().__init__("RequirementAnalysisWorkflow", "需求分析工作流")
        self.agents = {}
        self.results = {}
        
        # 初始化关键决策点组件
        self.decision_generator = DecisionPointGenerator()
        self.decision_ui = DecisionConfirmUI(mode="batch")
        self.decision_applier = DecisionApplier()
        self.decision_reporter = DecisionReportGenerator()
        
        self._initialize_agents()
    
    def get_workflow_steps(self) -> List[Dict[str, Any]]:
        """获取工作流步骤定义"""
        return [
            {"name": "requirement_collection", "description": "收集用户需求"},
            {"name": "requirement_analysis", "description": "分析需求可行性与条目化"},
            {"name": "requirement_validation", "description": "验证需求完整性"},
            {"name": "document_generation", "description": "生成需求规格说明书"}
        ]

    def _initialize_agents(self):
        """初始化所有Agent"""
        logger.info("初始化需求分析工作流的Agent...")
        
        # 创建Agent实例
        for agent_type, config in AGENT_CONFIGS.items():
            logger.info(f"创建 {config['name']}...")
            
            if agent_type == "requirement_collector":
                self.agents[agent_type] = RequirementCollectorAgent(**config)
            elif agent_type == "requirement_analyzer":
                self.agents[agent_type] = RequirementAnalyzerAgent(**config)
            elif agent_type == "requirement_validator":
                self.agents[agent_type] = RequirementValidatorAgent(**config)
            elif agent_type == "document_generator":
                self.agents[agent_type] = DocumentGeneratorAgent(**config)
    
    async def run(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """运行需求分析工作流"""
        user_input = input_data
        output_dir = kwargs.get("output_dir", "output")
        logger.info("开始执行需求分析工作流...")
        
        try:
            # 步骤1: 收集需求
            logger.info("步骤1: 收集需求...")
            collected_requirements = await self.agents["requirement_collector"].collect_requirements(user_input)
            self.results["collected_requirements"] = collected_requirements
            
            # 步骤2: 分析需求 - 建立结构化的需求条目
            logger.info("步骤2: 分析需求...")
            # 建立结构化的需求条目，便于后续架构设计关联
            requirement_items = {
                "raw_input": user_input,
                "functional_requirements": collected_requirements.get("functional_requirements", []),
                "key_features": collected_requirements.get("key_features", []),
                "non_functional_requirements": collected_requirements.get("non_functional_requirements", []),
                "business_requirements": collected_requirements.get("business_requirements", []),
                "requirement_entries": self._create_requirement_entries(collected_requirements)
            }
            analysis_results = await self.agents["requirement_analyzer"].analyze_feasibility(requirement_items)
            self.results["analysis_results"] = analysis_results
            
            # 步骤2.1: 初始评审要点生成（前置人工确认）
            # 在进入自动化验证循环前，先让人工确认关键方向，避免方向性错误导致的反复修复
            logger.info("步骤2.1: 生成初始评审要点...")
            initial_review_points = await self.agents["requirement_analyzer"].generate_review_points(requirement_items)
            self.results["initial_review_points"] = initial_review_points
            
            # 人工确认环节 (前置)
            if kwargs.get("interactive", False):
                await self._interactive_review(initial_review_points, requirement_items)
            else:
                logger.info(f"非交互模式，使用默认策略: {initial_review_points}")
                # 自动应用默认策略（简单记录日志，实际应用逻辑视具体实现而定）
                for point in initial_review_points:
                    if isinstance(point, dict):
                        logger.info(f"应用默认策略: {point.get('default')}")

            # 步骤2.5: 初始验证与闭环修复 (Loop)
            # 在进入人工确认前，先进行自动化的验证和修复
            logger.info("步骤2.5: 初始验证与闭环修复...")
            
            # 使用配置中的最大迭代次数，降低默认次数以避免死循环
            from config import REQUIREMENT_WORKFLOW_CONFIG
            max_refinement_loops = REQUIREMENT_WORKFLOW_CONFIG.get("max_iterations", 5)
            current_loop = 0
            
            # 初始化修复历史
            if "refinement_history" not in self.results:
                self.results["refinement_history"] = []

            while current_loop < max_refinement_loops:
                current_loop += 1
                logger.info(f"执行验证闭环 (第 {current_loop} 次)...")
                
                # 检查是否存在严重问题
                validation_check = await self.agents["requirement_validator"].validate_requirements(requirement_items)
                
                # 兼容旧接口与新接口返回结构
                is_valid = validation_check.get("is_valid", True)
                critical_issues = validation_check.get("critical_issues", [])
                
                if not is_valid or critical_issues:
                    # 优化：分类问题，区分阻断性（Blocker）和建议性（Suggestion）
                    # 只有阻断性问题才需要自动修复，建议性问题可以推迟到Review阶段
                    blockers = [i for i in critical_issues if "明确" not in i and "模糊" not in i] # 简单启发式：如果是模糊问题，可能无法自动修复
                    
                    # 如果全是模糊性问题，且已经尝试修复过一次，则不再死磕
                    if not blockers and current_loop > 1:
                        logger.warning("剩余问题多为模糊性描述，转为人工确认项，不再自动修复...")
                        if "remaining_issues" not in self.results:
                            self.results["remaining_issues"] = []
                        self.results["remaining_issues"].extend(critical_issues)
                        break

                    logger.warning(f"发现 {len(critical_issues)} 个严重问题，尝试自动修复...")
                    for issue in critical_issues:
                        logger.warning(f" - {issue}")
                    
                    # 记录当前问题
                    self.results["refinement_history"].append({
                        "loop": current_loop,
                        "issues": critical_issues,
                        "timestamp": datetime.now().isoformat()
                    })

                    # 如果是最后一次循环，不再尝试修复，而是将问题留给人工确认
                    if current_loop >= max_refinement_loops:
                        logger.warning("达到最大自动修复次数，将剩余问题转为人工确认项...")
                        
                        # 将剩余问题转换为Review Points
                        if "remaining_issues" not in self.results:
                            self.results["remaining_issues"] = []
                        self.results["remaining_issues"].extend(critical_issues)
                        break

                    # 调用分析Agent进行修复，传入历史记录以便Agent进行反思
                    refined_items = await self.agents["requirement_analyzer"].refine_requirements(
                        requirement_items, 
                        critical_issues,
                        history=self.results["refinement_history"]
                    )
                    
                    # 更新需求条目
                    requirement_items.update(refined_items)
                    
                    # 重新生成需求条目列表（如果需要）
                    if "requirement_entries" not in refined_items:
                        logger.info("根据更新的需求重新生成条目...")
                        requirement_items["requirement_entries"] = self._create_requirement_entries(requirement_items)
                else:
                    logger.info("验证通过，无严重阻断性问题。")
                    break
            
            # 步骤2.6: 结构化验证并生成关键决策点
            logger.info("步骤2.6: 结构化验证并生成关键决策点...")
            
            # 执行结构化验证
            structured_validation = await self.agents["requirement_validator"].validate_for_decisions(
                requirement_items
            )
            self.results["structured_validation"] = structured_validation
            
            # 生成关键决策点
            decisions = self.decision_generator.generate_from_validation(
                structured_validation,
                requirement_items
            )
            
            logger.info(f"生成了 {len(decisions)} 个关键决策点")
            
            # 步骤2.7: 产品经理确认关键决策点
            if decisions:
                if kwargs.get("interactive", False):
                    logger.info("步骤2.7: 等待产品经理确认关键决策点...")
                    decisions = await self.decision_ui.confirm(decisions)
                else:
                    # 非交互模式，使用默认策略
                    logger.info("步骤2.7: 非交互模式，使用默认策略...")
                    for decision in decisions:
                        decision.select_default()
                
                # 应用决策结果到需求项
                requirement_items = self.decision_applier.apply(decisions, requirement_items)
                
                # 记录决策结果
                self.results["key_decisions"] = [d.to_dict() for d in decisions]
                
                # 生成决策报告
                decision_report = self.decision_reporter.generate_markdown(decisions)
                self.results["decision_report"] = decision_report
            else:
                logger.info("无关键决策点需要确认")
                self.results["key_decisions"] = []
            
            # 步骤2.8: 生成评审要点并进行人工确认（保留兼容旧逻辑）
            logger.info("步骤2.8: 生成关键评审要点...")
            review_points = await self.agents["requirement_analyzer"].generate_review_points(requirement_items)
            
            # 如果存在未解决的验证问题，将其强制加入评审要点
            if critical_issues:
                for issue in critical_issues:
                    review_points.insert(0, {
                        "point": f"【遗留风险】{issue}",
                        "default": "需人工介入决策或接受风险"
                    })
            
            self.results["review_points"] = review_points
            
            # 人工确认环节
            if kwargs.get("interactive", False):
                print("\n" + "="*50)
                print("【人工确认环节】关键决策点与默认策略：")
                if isinstance(review_points, list):
                    for i, item in enumerate(review_points):
                        if isinstance(item, dict):
                            point = item.get("point", "")
                            default = item.get("default", "无")
                            print(f"{i+1}. {point}")
                            print(f"   [默认策略]: {default}")
                        else:
                            # 兼容旧格式（纯字符串）
                            print(f"{i+1}. {item}")
                else:
                    print(review_points)
                print("="*50)
                print("说明：输入 'y' 确认通过（使用默认策略），输入 'n' 提供反馈，直接回车使用默认配置继续。")
                
                # 在某些环境下 input 可能不可用，添加保护
                try:
                    confirm = input("\n请确认以上要点是否已解决或接受？(y/n/default[enter]): ").strip().lower()
                    
                    if confirm in ['', 'default']:
                        logger.info("用户选择使用默认配置继续")
                        # 可以在这里添加默认处理逻辑
                    elif confirm not in ['y', 'yes', 'c', 'continue']:
                        feedback = input("请输入您的反馈或修改意见：")
                        self.results["user_feedback"] = feedback
                        logger.info(f"用户反馈: {feedback}")
                        # 将反馈添加到需求条目中作为备注
                        requirement_items["user_feedback"] = feedback
                        
                        # 如果用户有反馈，可能需要重新分析或更新需求
                        # 这里简单地将反馈记录下来，实际场景可能需要循环确认
                except EOFError:
                    logger.warning("无法获取用户输入，跳过确认，默认继续")
            else:
                logger.info(f"非交互模式或自动确认，生成的评审要点: {review_points}")

            # 步骤3: 验证需求 - 全面验证（正确性、完整性、一致性、测试用例）
            logger.info("步骤3: 验证需求...")
            validator = self.agents["requirement_validator"]
            
            # 并行执行验证任务
            validation_task = validator.validate_correctness(requirement_items)
            completeness_task = validator.validate_completeness(requirement_items)
            consistency_task = validator.validate_consistency(requirement_items)
            test_cases_task = validator.generate_test_cases(requirement_items)
            
            v_res, c_res, s_res, t_res = await asyncio.gather(
                validation_task, 
                completeness_task, 
                consistency_task, 
                test_cases_task
            )
            
            validation_results = {
                "correctness": v_res.get("validation_results", ""),
                "completeness": c_res.get("completeness_validation", ""),
                "consistency": s_res.get("consistency_validation", ""),
                "test_cases": t_res.get("test_cases", ""),
                "timestamp": datetime.now().isoformat()
            }
            self.results["validation_results"] = validation_results
            
            # 存储结构化的需求条目供架构设计使用
            self.results["requirement_items"] = requirement_items
            
            # 步骤4: 生成文档
            logger.info("步骤4: 生成需求文档...")
            
            # 合并所有结果用于文档生成
            document_data = {
                "collected_requirements": requirement_items,
                "analysis_results": analysis_results,
                "validation_results": validation_results,
                "user_input": user_input,
                "requirement_entries": requirement_items.get("requirement_entries", [])
            }
            
            requirement_document = await self.agents["document_generator"].generate_requirement_document(document_data)
            self.results["requirement_document"] = requirement_document
            
            # 构建标准化的交付件 (Artifacts)
            artifacts = {
                "meta": {
                    "generated_at": datetime.now().isoformat(),
                    "version": "1.0"
                },
                "requirement_entries": requirement_items.get("requirement_entries", []),
                "raw_input": user_input,
                "constraints": {
                    "functional": requirement_items.get("functional_requirements", []),
                    "non_functional": requirement_items.get("non_functional_requirements", []),
                    "business": requirement_items.get("business_requirements", [])
                },
                "analysis_report": analysis_results,
                "refinement_history": self.results.get("refinement_history", []),  # 添加修复历史
                "user_feedback": self.results.get("user_feedback", None)
            }
            self.results["artifacts"] = artifacts
            
            # 保存结果
            self._save_results(output_dir=output_dir)
            
            logger.info("需求分析工作流执行完成！")
            return {
                "status": "success",
                "artifacts": artifacts,  # 交付给下一步的交付件
                "outputs": {             # 本步骤产生的输出件（不传递给下一步）
                    "validation_report": validation_results,
                    "requirement_document": requirement_document
                },
                "results": self.results,
                "output_file": self.results.get("output_file")
            }
            
        except Exception as e:
            logger.error(f"工作流执行失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _interactive_review(self, review_points, requirement_items):
        """交互式评审"""
        print("\n" + "="*50)
        print("【人工确认环节】关键决策点与默认策略：")
        if isinstance(review_points, list):
            for i, item in enumerate(review_points):
                if isinstance(item, dict):
                    point = item.get("point", "")
                    default = item.get("default", "无")
                    print(f"{i+1}. {point}")
                    print(f"   [默认策略]: {default}")
                else:
                    print(f"{i+1}. {item}")
        else:
            print(review_points)
        print("="*50)
        
        try:
            confirm = input("\n请确认以上要点是否已解决或接受？(y/n/default[enter]): ").strip().lower()
            if confirm not in ['y', 'yes', 'c', 'continue', '', 'default']:
                feedback = input("请输入您的反馈或修改意见：")
                self.results["user_feedback"] = feedback
                requirement_items["user_feedback"] = feedback
                logger.info(f"用户反馈: {feedback}")
        except EOFError:
            logger.warning("无法获取用户输入，跳过确认，默认继续")

    def _create_requirement_entries(self, collected_requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建结构化的需求条目，便于与架构设计关联"""
        entries = []
        
        # 处理功能需求
        functional_reqs = collected_requirements.get("functional_requirements", [])
        for i, req in enumerate(functional_reqs):
            entries.append({
                "id": f"FR-{i+1:03d}",
                "type": "functional",
                "description": req,
                "priority": "high" if i < 3 else "medium",
                "status": "analyzed"
            })
        
        # 处理非功能需求
        non_functional_reqs = collected_requirements.get("non_functional_requirements", [])
        for i, req in enumerate(non_functional_reqs):
            entries.append({
                "id": f"NFR-{i+1:03d}",
                "type": "non_functional",
                "description": req,
                "priority": "high",
                "status": "analyzed"
            })
        
        # 处理业务需求
        business_reqs = collected_requirements.get("business_requirements", [])
        for i, req in enumerate(business_reqs):
            entries.append({
                "id": f"BR-{i+1:03d}",
                "type": "business",
                "description": req,
                "priority": "high",
                "status": "analyzed"
            })
        
        return entries
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流状态"""
        requirement_entries = self.results.get("requirement_items", {}).get("requirement_entries", [])
        return {
            "agents_initialized": len(self.agents),
            "agents_status": {name: "active" for name in self.agents.keys()},
            "workflow_data_size": len(str(self.results)) if self.results else 0,
            "requirement_entries_count": len(requirement_entries),
            "requirement_entries": requirement_entries[:5]  # 只显示前5个作为示例
        }
    
    def _save_results(self, output_dir: str = "output"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        import json
        analysis = self.results.get("analysis_results", {})
        validation = self.results.get("validation_results", {})
        
        # 保存最小化JSON结果
        minimal = {
            "status": "success",
            "results": {
                "requirement_entries": self.results.get("requirement_items", {}).get("requirement_entries", []),
                "analysis_summary": analysis.get("feasibility_analysis", analysis),
                "validation_summary": validation
            }
        }
        json_filename = f"requirement_analysis_result_{timestamp}.json"
        json_path = os.path.join(output_dir, json_filename)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(minimal, f, ensure_ascii=False, indent=2)
            
        # 保存需求文档
        if 'requirement_document' in self.results:
            doc_filename = f"requirement_document_{timestamp}.md"
            doc_path = os.path.join(output_dir, doc_filename)
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(self.results['requirement_document'])
        
        # 保存验证报告
        if validation:
            val_md = [
                f"# 需求验证报告",
                f"生成时间: {timestamp}",
                f"\n## 1. 正确性验证",
                str(validation.get("correctness", "无")),
                f"\n## 2. 完整性验证",
                str(validation.get("completeness", "无")),
                f"\n## 3. 一致性验证",
                str(validation.get("consistency", "无")),
                f"\n## 4. 建议测试用例",
                str(validation.get("test_cases", "无"))
            ]
            val_filename = f"requirement_validation_report_{timestamp}.md"
            with open(os.path.join(output_dir, val_filename), 'w', encoding='utf-8') as f:
                f.write("\n".join(val_md))
        
        # 保存关键决策报告
        if 'decision_report' in self.results:
            decision_filename = f"product_decision_report_{timestamp}.md"
            with open(os.path.join(output_dir, decision_filename), 'w', encoding='utf-8') as f:
                f.write(self.results['decision_report'])
            logger.info(f"关键决策报告已保存: {decision_filename}")
        
        # 保存结构化验证结果
        if 'structured_validation' in self.results:
            sv = self.results['structured_validation']
            sv_filename = f"structured_validation_{timestamp}.json"
            with open(os.path.join(output_dir, sv_filename), 'w', encoding='utf-8') as f:
                json.dump(sv, f, ensure_ascii=False, indent=2)
                
        # 保存过程记录
        process_md = [
            "# 需求分析过程",
            f"开始时间: {datetime.now().isoformat()}",
            f"功能需求数量: {len(self.results.get('requirement_items', {}).get('functional_requirements', []))}",
            f"非功能需求数量: {len(self.results.get('requirement_items', {}).get('non_functional_requirements', []))}",
            f"业务需求数量: {len(self.results.get('requirement_items', {}).get('business_requirements', []))}"
        ]
        proc_filename = f"requirement_process_{timestamp}.md"
        with open(os.path.join(output_dir, proc_filename), 'w', encoding='utf-8') as f:
            f.write("\n".join(process_md))
        self.results["output_file"] = json_path
