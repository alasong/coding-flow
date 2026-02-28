"""自定义异常类"""

class CodingFlowError(Exception):
    """基础异常类"""
    
    def __init__(self, message: str, context: dict = None):
        self.message = message
        self.context = context or {}
        super().__init__(self.message)
    
    def __str__(self):
        if self.context:
            return f"{self.message} | context: {self.context}"
        return self.message


class LLMError(CodingFlowError):
    """LLM 调用错误"""
    pass


class AgentError(CodingFlowError):
    """Agent 执行错误"""
    pass


class WorkflowError(CodingFlowError):
    """工作流执行错误"""
    pass


class ValidationError(CodingFlowError):
    """验证错误"""
    pass


class AuthenticationError(CodingFlowError):
    """认证错误"""
    pass


class ConfigurationError(CodingFlowError):
    """配置错误"""
    pass
