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

class RequirementAnalysisWorkflow:
    """需求分析工作流 - 协调多个Agent完成需求分析任务"""
    
    def __init__(self):
        """初始化工作流"""
        self.agents = {}
        self.results = {}
        self._initialize_agents()
    
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
    
    async def run(self, user_input: str) -> Dict[str, Any]:
        """运行需求分析工作流"""
        logger.info("开始执行需求分析工作流...")
        
        try:
            # 步骤1: 收集需求
            logger.info("步骤1: 收集需求...")
            collected_requirements = await self.agents["requirement_collector"].collect_requirements(user_input)
            self.results["collected_requirements"] = collected_requirements
            
            # 步骤2: 分析需求 - 只传递核心需求信息
            logger.info("步骤2: 分析需求...")
            # 只提取关键信息传递给分析器，避免累积过多数据
            core_requirements = {
                "raw_input": user_input,
                "functional_requirements": collected_requirements.get("functional_requirements", []),
                "key_features": collected_requirements.get("key_features", [])
            }
            analysis_results = await self.agents["requirement_analyzer"].analyze_feasibility(core_requirements)
            self.results["analysis_results"] = analysis_results
            
            # 步骤3: 验证需求 - 只传递核心需求信息
            logger.info("步骤3: 验证需求...")
            validation_results = await self.agents["requirement_validator"].validate_correctness(core_requirements)
            self.results["validation_results"] = validation_results
            
            # 步骤4: 生成文档
            logger.info("步骤4: 生成需求文档...")
            
            # 合并所有结果用于文档生成，但控制数据量
            document_data = {
                "collected_requirements": core_requirements,  # 使用精简后的数据
                "analysis_results": analysis_results,
                "validation_results": validation_results,
                "user_input": user_input
            }
            
            requirement_document = await self.agents["document_generator"].generate_requirement_document(document_data)
            self.results["requirement_document"] = requirement_document
            
            # 保存结果
            self._save_results()
            
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
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流状态"""
        return {
            "agents_initialized": len(self.agents),
            "agents_status": {name: "active" for name in self.agents.keys()},
            "workflow_data_size": len(str(self.results)) if self.results else 0
        }
    
    def _save_results(self):
        """保存工作流结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "output"
        
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 保存JSON结果
        json_filename = f"requirement_analysis_{timestamp}.json"
        json_path = os.path.join(output_dir, json_filename)
        
        import json
        with open(json_path, 'w', encoding='utf-8') as f:
            # 确保所有数据都是JSON可序列化的
            serializable_results = {}
            for key, value in self.results.items():
                if key == "requirement_document":
                    serializable_results[key] = value
                else:
                    serializable_results[key] = value
            
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
        # 保存文档
        if 'requirement_document' in self.results:
            doc_filename = f"requirement_document_{timestamp}.md"
            doc_path = os.path.join(output_dir, doc_filename)
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(self.results['requirement_document'])
        
        self.results["output_file"] = json_path
        logger.info(f"结果已保存到 {output_dir} 目录")