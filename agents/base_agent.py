import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from ..models.base_model import BaseModel

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Agent基类 - 所有Agent的抽象基类"""
    
    def __init__(self, name: str, system_prompt: str, model: Optional[BaseModel] = None):
        """
        初始化Agent基类
        
        Args:
            name: Agent名称
            system_prompt: 系统提示词
            model: 模型实例（可选）
        """
        self.name = name
        self.system_prompt = system_prompt
        self.model = model or self._get_default_model()
        self.created_at = datetime.now()
        self.execution_count = 0
        
        logger.info(f"初始化Agent: {self.name}")
    
    def _get_default_model(self) -> BaseModel:
        """获取默认模型 - 如果模型不可用则抛出错误"""
        try:
            from ..models.dashscope_model import DashScopeModel
            return DashScopeModel()
        except ImportError as e:
            logger.error(f"DashScope模型导入失败: {e}")
            raise RuntimeError("无法导入DashScope模型。请确保已安装agentscope库并正确配置API密钥。")
        except Exception as e:
            logger.error(f"无法初始化DashScope模型: {e}")
            raise RuntimeError(f"模型初始化失败: {e}")
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行Agent的主要功能
        
        Args:
            input_data: 输入数据
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        pass
    
    def _call_model_with_streaming(self, prompt: str) -> str:
        """
        调用模型并处理流式响应
        
        Args:
            prompt: 提示词
            
        Returns:
            str: 模型响应内容
        """
        try:
            self.execution_count += 1
            logger.debug(f"调用模型: {self.name} (第{self.execution_count}次)")
            
            response = self.model.generate_response(prompt)
            
            # 处理流式响应
            if hasattr(response, '__iter__') and not isinstance(response, str):
                return self._process_streaming_response(response)
            else:
                # 优先使用text属性，避免将SimpleNamespace对象转换为字符串
                if hasattr(response, 'text'):
                    return response.text
                elif hasattr(response, '__dict__') and 'text' in response.__dict__:
                    return response.__dict__['text']
                else:
                    # 如果response没有text属性且没有__dict__，尝试其他方法
                    if hasattr(response, 'text'):
                        return response.text
                    else:
                        return str(response)
                
        except Exception as e:
            logger.error(f"模型调用失败: {e}")
            raise
    
    def _process_streaming_response(self, response_stream) -> str:
        """
        处理流式响应，避免内容重复累积
        
        Args:
            response_stream: 流式响应迭代器
            
        Returns:
            str: 处理后的完整内容
        """
        full_content = ""
        last_content = ""
        
        for chunk in response_stream:
            if isinstance(chunk, dict) and 'content' in chunk:
                current_content = chunk['content']
                # 只保留完整内容，避免增量累积
                if len(current_content) > len(last_content):
                    full_content = current_content
                last_content = current_content
            elif isinstance(chunk, str):
                # 如果是字符串，直接作为完整内容
                full_content = chunk
        
        return full_content
    
    def _extract_json_from_response(self, response: str, default_key: str = "result") -> Dict[str, Any]:
        """
        从响应文本中提取JSON内容
        
        Args:
            response: 响应文本
            default_key: 默认键名
            
        Returns:
            Dict[str, Any]: 提取的JSON数据
        """
        import json
        import re
        
        try:
            # 尝试查找JSON代码块
            json_pattern = r'```json\s*({[\s\S]*?})\s*```'
            match = re.search(json_pattern, response)
            
            if match:
                json_content = match.group(1)
                return json.loads(json_content)
            else:
                # 尝试查找其他JSON格式
                json_pattern = r'({\s*"[^"]*"\s*:\s*[^}]*})'
                matches = re.findall(json_pattern, response)
                if matches:
                    return json.loads(matches[0])
                
                # 如果没有找到JSON，返回默认结构
                return {default_key: response}
                
        except Exception as e:
            logger.error(f"JSON提取失败: {e}")
            return {default_key: response, "error": str(e)}
    
    def _create_error_result(self, error_message: str, input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        创建错误结果
        
        Args:
            error_message: 错误信息
            input_data: 输入数据（可选）
            
        Returns:
            Dict[str, Any]: 错误结果
        """
        return {
            "status": "failed",
            "error": error_message,
            "agent_name": self.name,
            "timestamp": datetime.now().isoformat(),
            "input_data": input_data
        }
    
    def _create_success_result(self, result_data: Dict[str, Any], input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        创建成功结果
        
        Args:
            result_data: 结果数据
            input_data: 输入数据（可选）
            
        Returns:
            Dict[str, Any]: 成功结果
        """
        return {
            "status": "completed",
            "result": result_data,
            "agent_name": self.name,
            "timestamp": datetime.now().isoformat(),
            "input_data": input_data,
            "execution_info": {
                "execution_count": self.execution_count,
                "created_at": self.created_at.isoformat()
            }
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        获取Agent信息
        
        Returns:
            Dict[str, Any]: Agent信息
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "system_prompt_length": len(self.system_prompt),
            "model_type": type(self.model).__name__,
            "created_at": self.created_at.isoformat(),
            "execution_count": self.execution_count,
            "description": self.__doc__ or "暂无描述"
        }
    
    def validate_input(self, input_data: Dict[str, Any], required_fields: List[str]) -> bool:
        """
        验证输入数据
        
        Args:
            input_data: 输入数据
            required_fields: 必需字段列表
            
        Returns:
            bool: 验证结果
        """
        if not input_data:
            logger.error("输入数据为空")
            return False
        
        missing_fields = []
        for field in required_fields:
            if field not in input_data or not input_data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            logger.error(f"缺少必需字段: {missing_fields}")
            return False
        
        return True
    
    def log_execution(self, level: str, message: str, extra_data: Optional[Dict[str, Any]] = None) -> None:
        """
        记录执行日志
        
        Args:
            level: 日志级别
            message: 日志消息
            extra_data: 额外数据（可选）
        """
        log_data = {
            "agent_name": self.name,
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