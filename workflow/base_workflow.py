import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

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
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工作流
        
        Args:
            input_data: 输入数据
            
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
            
            step_result["result"] = result
            step_result["status"] = "completed"
            step_result["end_time"] = datetime.now().isoformat()
            
            # 更新上下文
            context["steps"][step_name] = step_result
            if result and isinstance(result, dict):
                context["intermediate_results"][step_name] = result
            
            logger.info(f"步骤完成: {step_name}")
            return step_result
            
        except Exception as e:
            logger.error(f"步骤执行失败: {step_name}, 错误: {e}")
            step_result["status"] = "failed"
            step_result["error"] = str(e)
            step_result["end_time"] = datetime.now().isoformat()
            
            context["steps"][step_name] = step_result
            return step_result
    
    def _validate_workflow_input(self, input_data: Dict[str, Any], required_fields: List[str]) -> bool:
        """
        验证工作流输入
        
        Args:
            input_data: 输入数据
            required_fields: 必需字段列表
            
        Returns:
            bool: 验证结果
        """
        if not input_data:
            logger.error("工作流输入数据为空")
            return False
        
        missing_fields = []
        for field in required_fields:
            if field not in input_data or not input_data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            logger.error(f"工作流缺少必需字段: {missing_fields}")
            return False
        
        return True
    
    def _create_success_result(self, context: Dict[str, Any], final_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        创建成功结果
        
        Args:
            context: 工作流上下文
            final_result: 最终结果数据
            
        Returns:
            Dict[str, Any]: 成功结果
        """
        result = {
            "workflow_name": self.name,
            "status": "completed",
            "start_time": context["start_time"],
            "end_time": datetime.now().isoformat(),
            "steps": context["steps"],
            "execution_info": {
                "execution_count": self.execution_count,
                "created_at": self.created_at.isoformat()
            }
        }
        
        if final_result:
            result["final_result"] = final_result
        
        return result
    
    def _create_error_result(self, context: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """
        创建错误结果
        
        Args:
            context: 工作流上下文
            error_message: 错误信息
            
        Returns:
            Dict[str, Any]: 错误结果
        """
        return {
            "workflow_name": self.name,
            "status": "failed",
            "error": error_message,
            "start_time": context["start_time"],
            "end_time": datetime.now().isoformat(),
            "steps": context.get("steps", {}),
            "execution_info": {
                "execution_count": self.execution_count,
                "created_at": self.created_at.isoformat()
            }
        }
    
    def save_results(self, result: Dict[str, Any], output_dir: str = "output", 
                    file_prefix: str = "", save_json: bool = True) -> List[str]:
        """
        保存工作流结果
        
        Args:
            result: 工作流执行结果
            output_dir: 输出目录
            file_prefix: 文件前缀
            save_json: 是否保存JSON文件
            
        Returns:
            List[str]: 保存的文件路径列表
        """
        saved_files = []
        
        try:
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if save_json:
                # 保存JSON结果
                json_file = f"{output_dir}/{file_prefix}workflow_result_{timestamp}.json"
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                saved_files.append(json_file)
            
            logger.info(f"工作流结果已保存: {saved_files}")
            return saved_files
            
        except Exception as e:
            logger.error(f"保存工作流结果失败: {e}")
            return saved_files
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """
        获取工作流信息
        
        Returns:
            Dict[str, Any]: 工作流信息
        """
        return {
            "name": self.name,
            "description": self.description,
            "type": self.__class__.__name__,
            "created_at": self.created_at.isoformat(),
            "execution_count": self.execution_count,
            "steps": self.get_workflow_steps(),
            "history_count": len(self.workflow_history)
        }
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """
        获取执行统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        if not self.workflow_history:
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "success_rate": 0.0,
                "average_execution_time": 0.0
            }
        
        total_executions = len(self.workflow_history)
        successful_executions = sum(1 for r in self.workflow_history if r.get("status") == "completed")
        failed_executions = total_executions - successful_executions
        success_rate = successful_executions / total_executions if total_executions > 0 else 0.0
        
        # 计算平均执行时间
        execution_times = []
        for result in self.workflow_history:
            if result.get("start_time") and result.get("end_time"):
                try:
                    start_time = datetime.fromisoformat(result["start_time"])
                    end_time = datetime.fromisoformat(result["end_time"])
                    execution_time = (end_time - start_time).total_seconds()
                    execution_times.append(execution_time)
                except Exception as e:
                    logger.warning(f"计算执行时间失败: {e}")
        
        average_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0.0
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "success_rate": success_rate,
            "average_execution_time": average_execution_time
        }
    
    def add_to_history(self, result: Dict[str, Any]) -> None:
        """
        添加执行结果到历史记录
        
        Args:
            result: 执行结果
        """
        self.workflow_history.append({
            "timestamp": datetime.now().isoformat(),
            "result": result
        })
        
        # 限制历史记录数量，避免内存溢出
        max_history = 100
        if len(self.workflow_history) > max_history:
            self.workflow_history = self.workflow_history[-max_history:]
    
    def log_workflow_event(self, level: str, message: str, extra_data: Optional[Dict[str, Any]] = None) -> None:
        """
        记录工作流事件
        
        Args:
            level: 日志级别
            message: 日志消息
            extra_data: 额外数据（可选）
        """
        log_data = {
            "workflow_name": self.name,
            "execution_count": self.execution_count,
            "message": message
        }
        
        if extra_data:
            log_data.update(extra_data)
        
        if level == "debug":
            logger.debug(log_data)
        elif level == "info":
            logger.info(log_data)
        elif level == "warning":
            logger.warning(log_data)
        elif level == "error":
            logger.error(log_data)
        else:
            logger.info(log_data)