"""
模拟模型类 - 用于测试和演示
"""

class MockModel:
    """模拟的AI模型，返回预设的响应"""
    
    def __init__(self, model_name="mock-model"):
        self.model_name = model_name
        self.call_count = 0
        
    def __call__(self, prompt):
        """模拟模型调用"""
        self.call_count += 1
        
        # 根据prompt内容返回不同的模拟响应
        if "需求" in prompt or "requirement" in prompt.lower():
            return self._generate_requirement_response()
        elif "分析" in prompt or "analyze" in prompt.lower():
            return self._generate_analysis_response()
        elif "验证" in prompt or "validate" in prompt.lower():
            return self._generate_validation_response()
        elif "文档" in prompt or "document" in prompt.lower():
            return self._generate_document_response()
        else:
            return self._generate_default_response()
    
    def _generate_requirement_response(self):
        """生成需求收集的模拟响应"""
        import types
        response = types.SimpleNamespace()
        response.text = """
        功能需求：
        1. 用户注册和登录功能
        2. 课程管理系统
        3. 视频播放功能
        4. 学习进度跟踪
        5. 作业提交系统
        
        非功能需求：
        1. 系统性能要求
        2. 安全性要求
        3. 可用性要求
        
        约束：
        1. 开发时间限制
        2. 预算限制
        """
        return response
    
    def _generate_analysis_response(self):
        """生成需求分析的模拟响应"""
        import types
        response = types.SimpleNamespace()
        response.text = """
        可行性分析：
        1. 技术可行性：高
        2. 经济可行性：中
        3. 时间可行性：中
        
        风险评估：
        1. 技术风险：低
        2. 进度风险：中
        3. 成本风险：低
        """
        return response
    
    def _generate_validation_response(self):
        """生成需求验证的模拟响应"""
        import types
        response = types.SimpleNamespace()
        response.text = """
        验证结果：
        1. 需求完整性：85%
        2. 需求一致性：90%
        3. 需求可测试性：80%
        
        建议改进：
        1. 补充详细的性能指标
        2. 明确安全要求细节
        """
        return response
    
    def _generate_document_response(self):
        """生成文档创建的模拟响应"""
        import types
        response = types.SimpleNamespace()
        response.text = """
        # 软件需求规格说明书
        
        ## 1. 引言
        本文档描述了在线学习平台的需求规格。
        
        ## 2. 功能需求
        - 用户管理
        - 课程管理
        - 视频播放
        - 进度跟踪
        
        ## 3. 非功能需求
        - 性能要求
        - 安全要求
        - 可用性要求
        
        ## 4. 验收标准
        详细描述了系统验收的具体标准。
        """
        return response
    
    def _generate_default_response(self):
        """生成默认响应"""
        import types
        response = types.SimpleNamespace()
        response.text = "这是一个模拟的AI响应。"
        return response