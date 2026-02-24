import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
import asyncio

logger = logging.getLogger(__name__)

class BaseWorkflow(ABC):
    """工作流基类 - 所有工作流的抽象基类"""
    
    def __init__(self, name: str, description: str = ""):
        """
        初始化工作流基类
        
        Args:
            name: 工作流名称
            description: 工作流描述
        """
        self.name = name
        self.description = description
        self.created_at = datetime.now()
        self.execution_count = 0
        self.workflow_history = []
        
        logger.info(f"初始化工作流: {self.name}")
    
    @abstractmethod
    async def run(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        异步执行工作流
        
        Args:
            input_data: 输入数据
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        pass
    
    @abstractmethod
    def get_workflow_steps(self) -> List[Dict[str, Any]]:
        """
        获取工作流步骤定义
        
        Returns:
            List[Dict[str, Any]]: 步骤定义列表
        """
        pass
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        同步执行工作流（包装异步方法）
        
        Args:
            input_data: 输入数据
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        return asyncio.run(self.run(input_data))
    
    def _create_workflow_context(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建工作流上下文
        
        Args:
            input_data: 输入数据
            
        Returns:
            Dict[str, Any]: 工作流上下文
        """
        return {
            "workflow_name": self.name,
            "workflow_id": f"{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "start_time": datetime.now().isoformat(),
            "input_data": input_data,
            "steps": {},
            "intermediate_results": {},
            "metadata": {
                "created_at": self.created_at.isoformat(),
                "execution_count": self.execution_count
            }
        }
    
    def _execute_step(self, step_name: str, step_function, context: Dict[str, Any], 
                     input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行单个步骤
        
        Args:
            step_name: 步骤名称
            step_function: 步骤执行函数
            context: 工作流上下文
            input_data: 步骤输入数据
            
        Returns:
            Dict[str, Any]: 步骤执行结果
        """
        logger.info(f"执行步骤: {step_name}")
        
        step_result = {
            "step_name": step_name,
            "start_time": datetime.now().isoformat(),
            "status": "in_progress",
            "input_data": input_data
        }
        
        try:
            # 执行步骤函数
            if input_data:
                result = step_function(input_data)
            else:
                result = step_function()
            
            step_result["status"] = "completed"
            step_result["result"] = result
            step_result["end_time"] = datetime.now().isoformat()
            
            return step_result
            
        except Exception as e:
            logger.error(f"步骤执行失败: {e}")
            step_result["status"] = "failed"
            step_result["error"] = str(e)
            step_result["end_time"] = datetime.now().isoformat()
            raise
