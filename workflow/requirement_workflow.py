"""
需求分析工作流 - 使用AgentScope 1.0.7兼容版本
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Any

# 导入Agent类
from agents.requirement_collector import RequirementCollectorAgent
from agents.requirement_analyzer import RequirementAnalyzerAgent
from agents.requirement_validator import RequirementValidatorAgent
from agents.document_generator import DocumentGeneratorAgent

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
            
            # 步骤2.5: 生成评审要点并进行人工确认
            logger.info("步骤2.5: 生成关键评审要点...")
            review_points = await self.agents["requirement_analyzer"].generate_review_points(requirement_items)
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

            # 步骤3: 验证需求 - 基于需求条目进行验证
            logger.info("步骤3: 验证需求...")
            validation_results = await self.agents["requirement_validator"].validate_correctness(requirement_items)
            self.results["validation_results"] = validation_results
            
            # 存储结构化的需求条目供架构设计使用
            self.results["requirement_items"] = requirement_items
            
            # 步骤4: 生成文档
            logger.info("步骤4: 生成需求文档...")
            
            # 合并所有结果用于文档生成，包含结构化的需求条目
            document_data = {
                "collected_requirements": requirement_items,  # 使用结构化的需求条目
                "analysis_results": analysis_results,
                "validation_results": validation_results,
                "user_input": user_input,
                "requirement_entries": requirement_items.get("requirement_entries", [])
            }
            
            requirement_document = await self.agents["document_generator"].generate_requirement_document(document_data)
            self.results["requirement_document"] = requirement_document
            
            # 保存结果
            self._save_results(output_dir=output_dir)
            
            logger.info("需求分析工作流执行完成！")
            return {
                "status": "success",
                "results": self.results,
                "output_file": self.results.get("output_file")
            }
            
        except Exception as e:
            logger.error(f"工作流执行失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
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
        minimal = {
            "status": "success",
            "results": {
                "requirement_entries": self.results.get("requirement_items", {}).get("requirement_entries", []),
                "analysis_summary": analysis.get("feasibility_analysis", analysis),
                "validation_summary": validation.get("validation_results", validation)
            }
        }
        json_filename = f"requirement_analysis_result_{timestamp}.json"
        json_path = os.path.join(output_dir, json_filename)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(minimal, f, ensure_ascii=False, indent=2)
        if 'requirement_document' in self.results:
            doc_filename = f"requirement_document_{timestamp}.md"
            doc_path = os.path.join(output_dir, doc_filename)
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(self.results['requirement_document'])
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
