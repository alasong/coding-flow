"""
架构分析Agent - 负责系统架构设计和技术选型
"""

from agentscope.agent import AgentBase
from typing import Dict, List, Any
import json
import logging
from datetime import datetime
import asyncio
from config import DASHSCOPE_API_KEY, OPENAI_API_KEY, DEFAULT_MODEL

logger = logging.getLogger(__name__)

class ArchitectureAnalyzerAgent(AgentBase):
    """架构分析Agent - 负责系统架构设计和技术选型"""
    
    def __init__(self, name: str, model_config_name: str):
        super().__init__()
        self.name = name
        self.model_config_name = model_config_name
        
        # 配置真实的大模型API
        if DASHSCOPE_API_KEY or OPENAI_API_KEY:
            try:
                if DASHSCOPE_API_KEY:
                    from agentscope.model import DashScopeChatModel
                    self.model = DashScopeChatModel(
                        model_name="qwen-turbo",
                        api_key=DASHSCOPE_API_KEY,
                        generate_kwargs={"temperature": 0.3, "max_tokens": 2000}
                    )
                    logger.info(f"[{self.name}] 成功初始化DashScope模型: qwen-turbo")
                else:
                    from agentscope.model import OpenAIChatModel
                    self.model = OpenAIChatModel(
                        model_name=DEFAULT_MODEL,
                        api_key=OPENAI_API_KEY,
                        generate_kwargs={"temperature": 0.3, "max_tokens": 2000}
                    )
                    logger.info(f"[{self.name}] 成功初始化OpenAI模型: {DEFAULT_MODEL}")
                    
            except Exception as e:
                logger.error(f"[{self.name}] 初始化真实模型失败: {e}")
                raise RuntimeError(f"模型初始化失败: {e}")
        else:
            logger.warning(f"[{self.name}] 未配置API密钥，使用离线默认设计")
            self.model = None
    
    def _extract_json(self, content: str, expected_type=dict):
        """提取并解析JSON"""
        try:
            # 1. 尝试提取代码块
            import re
            code_block_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if code_block_match:
                json_str = code_block_match.group(1)
                return json.loads(json_str)
            
            code_block_match_2 = re.search(r'```\s*([\s\S]*?)\s*```', content)
            if code_block_match_2:
                try:
                    json_str = code_block_match_2.group(1)
                    return json.loads(json_str)
                except:
                    pass

            # 2. 尝试提取最外层JSON对象或数组
            if expected_type == list:
                match = re.search(r'\[[\s\S]*\]', content)
            else:
                match = re.search(r'\{[\s\S]*\}', content)
                
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
                
            # 3. 尝试直接解析
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.debug(f"原始内容: {content}")
            return None
        except Exception as e:
            logger.error(f"JSON提取未知错误: {e}")
            return None

    async def propose_initial_architectures(self, requirements: Dict[str, Any], count: int = 3) -> List[Dict[str, Any]]:
        """基于需求提出多套初始架构方案"""
        logger.info(f"[{self.name}] 开始生成 {count} 套初始架构方案")
        
        requirement_entries = requirements.get('requirement_entries', [])
        req_analysis_text = self._build_requirement_analysis_text(requirement_entries)
        
        prompt = f"""
        基于以下详细需求分析，请设计 {count} 套不同的系统架构初步方案（Architecture Proposals），供用户选择：
        
        {req_analysis_text}
        
        请针对该项目特点（如并发量、安全性、开发成本等权衡），提供 {count} 套有明显差异的架构思路。
        这些方案应该覆盖不同的架构风格和技术取舍，例如：
        - 方案1：注重高性能和可扩展性的分布式架构
        - 方案2：注重快速交付和低维护成本的单体/模块化单体架构
        - 方案3：采用新兴技术栈（如Serverless）的云原生架构
        
        每套方案请包含：
        1. 方案名称与核心理念
        2. 关键技术栈（前端、后端、数据库）
        3. 适用场景与优势（Pros）
        4. 潜在风险与劣势（Cons）
        5. 对关键需求（特别是高优先级的FR和NFR）的响应策略
        
        请以JSON列表格式返回，每个元素是一套方案，必须严格包含以下字段：
        - id: 方案ID (如 proposal_1)
        - name: 方案名称
        - description: 核心理念描述
        - tech_stack: 关键技术栈描述
        - pros: 优势列表 [str]
        - cons: 劣势列表 [str]
        """
        
        if not getattr(self, "model", None):
            # 离线模式返回默认模拟数据
            return [
                {
                    "id": "proposal_a",
                    "name": "高性能微服务架构",
                    "description": "采用Spring Cloud/K8s体系，服务拆分细致，适合高并发场景。",
                    "tech_stack": "Java/Spring Boot, React, MySQL, Redis, Kafka",
                    "pros": ["高扩展性", "故障隔离", "技术成熟"],
                    "cons": ["运维复杂", "分布式事务难处理", "初期开发成本高"]
                },
                {
                    "id": "proposal_b",
                    "name": "敏捷模块化单体架构",
                    "description": "基于Django/Rails的单体应用，内部模块化，适合快速迭代。",
                    "tech_stack": "Python/Django, Vue.js, PostgreSQL",
                    "pros": ["开发速度快", "部署简单", "调试方便"],
                    "cons": ["水平扩展受限", "代码库膨胀后难以维护"]
                }
            ]
            
        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        
        proposals = self._extract_json(content, expected_type=list)
        if proposals:
            # 确保每个方案有ID
            for idx, p in enumerate(proposals):
                if "id" not in p: p["id"] = f"proposal_{idx+1}"
            return proposals
        else:
            logger.warning(f"[{self.name}] 解析多套架构方案失败")
            return []

    async def refine_architecture(self, requirements: Dict[str, Any], current_architecture: Dict[str, Any], validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """根据验证结果优化架构"""
        logger.info(f"[{self.name}] 开始根据验证结果优化架构")
        
        # 提取验证反馈
        key_issues = validation_result.get("key_issues", [])
        recommendations = validation_result.get("recommendations", [])
        
        if not key_issues and not recommendations:
            logger.info(f"[{self.name}] 没有发现严重问题，无需优化")
            return current_architecture

        # 准备优化上下文
        issues_text = "\n".join([f"- 问题: {issue.get('issue', '未知问题')} (严重性: {issue.get('severity', '未知')}) - 描述: {issue.get('description', '')}" for issue in key_issues])
        recommendations_text = "\n".join([f"- 建议: {rec.get('description', '')} (优先级: {rec.get('priority', '未知')})" for rec in recommendations])
        
        prompt = f"""
        你需要根据以下验证反馈，对现有的系统架构进行优化和修复。
        
        现有架构设计（摘要）:
        - 模式: {current_architecture.get('system_architecture', {}).get('architecture_pattern', '未知')}
        - 技术栈: {json.dumps(current_architecture.get('technology_stack', {}), ensure_ascii=False)}
        
        验证反馈:
        【发现的问题】
        {issues_text}
        
        【改进建议】
        {recommendations_text}
        
        请针对上述问题和建议，修改和完善架构设计。你需要返回一个完整的、更新后的架构设计JSON。
        重点关注：
        1. 解决所有 High/Critical 级别的严重问题。
        2. 采纳合理的改进建议。
        3. 保持原有架构中合理的部分不变。
        
        请以JSON格式返回更新后的完整架构设计（结构与之前一致，包含 system_architecture, database_design, api_architecture 等字段）。
        """
        
        if not getattr(self, "model", None):
             # 离线模式：简单合并建议到summary
            new_arch = current_architecture.copy()
            new_arch["refinement_note"] = "Based on validation, offline mode simulated refinement."
            return new_arch

        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        
        refined_arch = self._extract_json(content)
        if refined_arch:
            # 确保保留必要的元数据
            if "selected_proposal" in current_architecture and "selected_proposal" not in refined_arch:
                refined_arch["selected_proposal"] = current_architecture["selected_proposal"]
            return refined_arch
        else:
            logger.warning(f"[{self.name}] 无法解析优化后的架构JSON，返回原架构")
            return current_architecture

    async def analyze_system_architecture(self, requirements: Dict[str, Any], selected_proposal: Dict[str, Any] = None) -> Dict[str, Any]:
        """分析系统架构（支持基于选定方案细化）- 采用多阶段（Multi-Bucket）生成策略以消除幻觉"""
        logger.info(f"[{self.name}] 开始分析系统架构 (基于方案: {selected_proposal.get('name', '自动推导') if selected_proposal else '自动推导'})")
        
        # 提取关键信息
        functional_reqs = requirements.get('functional_requirements', [])
        non_functional_reqs = requirements.get('non_functional_requirements', [])
        constraints = requirements.get('constraints', [])
        
        # 阶段 1: 领域实体提取 (Domain Entity Extraction)
        # 仅关注功能需求，提取核心业务名词，明确业务边界
        domain_entities = await self._extract_domain_entities(functional_reqs)
        logger.info(f"[{self.name}] 提取的领域实体: {domain_entities}")
        
        # 阶段 2: 组件映射 (Component Mapping)
        # 仅基于提取的实体生成组件，严禁发散
        system_components = await self._map_entities_to_components(domain_entities, functional_reqs)
        logger.info(f"[{self.name}] 生成的系统组件: {[c['name'] for c in system_components]}")
        
        # 阶段 3: 技术栈融合 (Tech Stack Fusion)
        # 将选定的技术栈注入到组件中，并完善架构细节
        architecture_design = await self._fuse_tech_stack(
            system_components, 
            selected_proposal, 
            functional_reqs, 
            non_functional_reqs, 
            constraints
        )
        
        return architecture_design

    async def _extract_domain_entities(self, functional_reqs: List[str]) -> List[str]:
        """阶段 1: 从功能需求中提取核心领域实体"""
        if not getattr(self, "model", None):
            return ["User", "System"] # 离线默认
            
        prompt = f"""
        任务：从以下功能需求中提取核心业务实体（Domain Entities）。
        
        功能需求：
        {chr(10).join(f'- {req}' for req in functional_reqs)}
        
        【严格约束】
        1. 仅提取需求中明确出现的名词，不要臆造。
        2. **严禁**联想需求中未提及的实体。
        3. 忽略通用技术名词（如“数据库”、“系统”、“接口”）。
        4. 输出格式为JSON字符串数组。
        
        示例输入：
        - 借阅者可以查询图书
        - 管理员可以上架新书
        示例输出：
        ["Borrower", "Book", "Administrator"]
        """
        
        try:
            response = await self.model([{"role": "user", "content": prompt}])
            content = await self._process_model_response(response)
            entities = self._extract_json(content, expected_type=list)
            return entities if entities else []
        except Exception as e:
            logger.warning(f"[{self.name}] 领域实体提取失败: {e}")
            return []

    async def _map_entities_to_components(self, entities: List[str], functional_reqs: List[str]) -> List[Dict[str, Any]]:
        """阶段 2: 将实体映射为系统组件"""
        if not getattr(self, "model", None):
            return [{"name": "CoreService", "description": "核心业务服务", "mechanisms": ["Basic CRUD"]}]
            
        prompt = f"""
        任务：基于核心业务实体，设计系统组件（Services/Modules）及其关键机制。
        
        核心实体：
        {json.dumps(entities, ensure_ascii=False)}
        
        功能需求上下文：
        {chr(10).join(f'- {req}' for req in functional_reqs[:10])}
        
        【设计要求】
        1. 每个组件必须对应一个或多个核心实体。
        2. **绝对禁止**创建与核心实体无关的组件。
        3. 必须包含一个 API Gateway（如果适用）。
        4. 【关键机制设计】：为每个组件设计 1-3 个具体的架构机制（Architectural Mechanisms），以提升系统的鲁棒性、性能或可维护性。
           - 例如：高频读取组件可能需要 "Read-Through Caching"。
           - 例如：复杂事务组件可能需要 "Saga Pattern"。
           - 避免使用笼统的 "High Performance"，请使用具体的设计模式名称。
        
        请以JSON列表格式返回组件，每个组件包含：
        - name: 组件名称
        - description: 职责描述
        - mechanisms: [str] 关键机制列表 (e.g., ["Cache-Aside", "Rate Limiting"])
        """
        
        try:
            response = await self.model([{"role": "user", "content": prompt}])
            content = await self._process_model_response(response)
            components = self._extract_json(content, expected_type=list)
            return components if components else []
        except Exception as e:
            logger.warning(f"[{self.name}] 组件映射失败: {e}")
            return []

    async def _fuse_tech_stack(self, components: List[Dict[str, Any]], selected_proposal: Dict[str, Any], 
                              functional_reqs: List[str], non_functional_reqs: List[str], constraints: List[str]) -> Dict[str, Any]:
        """阶段 3: 融合技术栈生成完整架构"""
        
        # 强制使用选定方案的技术栈
        tech_stack_context = ""
        if selected_proposal:
            tech_stack_context = f"""
            【强制技术栈】
            必须严格使用以下技术栈，不得更改：
            {json.dumps(selected_proposal.get('tech_stack', {}), ensure_ascii=False)}
            """
            
        components_context = json.dumps(components, ensure_ascii=False)
        
        prompt = f"""
        任务：基于已确定的系统组件和技术栈，生成完整的系统架构设计。
        
        已确定的系统组件（不可增减）：
        {components_context}
        
        {tech_stack_context}
        
        功能需求：
        {chr(10).join(f'- {req}' for req in functional_reqs[:10])}
        
        非功能需求：
        {chr(10).join(f'- {req}' for req in non_functional_reqs[:5])}
        
        【设计重点】
        请详细阐述每个组件的 **"机制 (Mechanisms)"** 如何落地实现。
        例如，如果组件定义了 "Cache-Aside"，请在 system_components 详情中说明如何结合选定的 Redis 技术栈实现该机制。
        
        请生成详细架构设计JSON，包含：
        - architecture_pattern: 架构模式
        - technology_stack: 技术栈（必须与强制技术栈一致）
        - system_components: 系统组件详情（必须包含 mechanisms 字段及其实现说明）
        - deployment_architecture: 部署架构
        - performance_considerations: 性能考虑
        - scalability_design: 扩展性设计
        - security_architecture: 安全架构
        - monitoring_architecture: 监控架构
        - analysis_summary: 分析总结
        """
        
        if not getattr(self, "model", None):
            return self._generate_default_architecture_analysis()
            
        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        
        design = self._extract_json(content)
        
        # Code-Level Override: 再次强制覆盖技术栈，确保万无一失
        if design and selected_proposal and 'tech_stack' in selected_proposal:
             # 注意：selected_proposal['tech_stack'] 可能是字符串也可能是字典，需要适配
             proposal_stack = selected_proposal['tech_stack']
             if isinstance(proposal_stack, str):
                 # 如果是字符串描述，暂时无法精确覆盖字典，但前面的Prompt应该已经生效
                 pass 
             elif isinstance(proposal_stack, dict):
                 design['technology_stack'] = proposal_stack
                 
        return design if design else self._generate_default_architecture_analysis()

    
    def _build_requirement_analysis_text(self, requirement_entries: List[Dict[str, Any]]) -> str:
        """构建需求分析文本"""
        if not requirement_entries:
            return "暂无具体需求条目"
        
        fr_reqs = [req for req in requirement_entries if req.get('id', '').startswith('FR-')]
        nfr_reqs = [req for req in requirement_entries if req.get('id', '').startswith('NFR-')]
        
        analysis_text = f"需求分析总结：\n"
        analysis_text += f"总需求数：{len(requirement_entries)}\n"
        analysis_text += f"功能需求：{len(fr_reqs)}个\n"
        analysis_text += f"非功能需求：{len(nfr_reqs)}个\n\n"
        
        if fr_reqs:
            analysis_text += "功能需求详情：\n"
            for req in fr_reqs:
                analysis_text += f"- {req.get('id', '')}: {req.get('description', '')} (优先级：{req.get('priority', '中')})\n"
        
        if nfr_reqs:
            analysis_text += "\n非功能需求详情：\n"
            for req in nfr_reqs:
                analysis_text += f"- {req.get('id', '')}: {req.get('description', '')} (优先级：{req.get('priority', '中')})\n"
        
        return analysis_text
    
    async def design_database_schema(self, requirements: Dict[str, Any], system_arch: Dict[str, Any] = None) -> Dict[str, Any]:
        """设计数据库架构（支持参考系统架构上下文）"""
        logger.info(f"[{self.name}] 开始设计数据库架构")
        
        functional_reqs = requirements.get('functional_requirements', [])
        
        # 构建系统组件上下文
        component_context = ""
        if system_arch and 'system_components' in system_arch:
            components = system_arch.get('system_components', [])
            component_context = f"""
            【已确定的系统组件】
            以下是系统架构中包含的业务组件，请仅为这些组件设计必要的数据库表：
            {json.dumps([c.get('name') for c in components], ensure_ascii=False)}
            """
            
        prompt = f"""
        基于以下功能需求和系统组件，设计数据库架构：
        
        功能需求：
        {chr(10).join(f'- {req}' for req in functional_reqs[:15]) if functional_reqs else '暂无具体功能需求'}
        
        {component_context}
        
        【重要原则】
        1. 数据表设计必须严格对应功能需求和系统组件。
        2. **严禁**生成与上述组件无关的表！
        3. 如果需求很简单，数据库设计也应保持简单。
        4. 表名和字段名请使用英文。
        
        请提供详细的数据库设计方案，包括：
        1. 数据库类型选择（关系型/非关系型/混合）
        2. 主要数据表设计（仅包含必要的业务表）
        3. 表结构和字段定义
        4. 主键和外键关系
        5. 索引设计策略
        6. 数据分区和分表策略
        7. 数据备份和恢复策略
        8. 数据库性能优化方案
        
        请以JSON格式返回，包含以下字段：
        - database_type: 数据库类型
        - tables: 数据表列表
        - relationships: 表关系
        - indexing_strategy: 索引策略
        - optimization_strategy: 优化策略
        - backup_strategy: 备份策略
        """
        
        if not getattr(self, "model", None):
            return self._generate_default_database_design(requirements)
        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        
        database_design = self._extract_json(content)
        if not database_design:
            logger.warning(f"[{self.name}] 解析数据库设计JSON失败，使用默认设计")
            database_design = self._generate_default_database_design(requirements)
        
        return database_design

    async def analyze_architecture(self, requirements: Dict[str, Any], selected_proposal: Dict[str, Any] = None) -> Dict[str, Any]:
        """分析架构 - 主方法"""
        logger.info(f"[{self.name}] 开始分析架构")
        
        # 并行执行三个分析任务
        # 注意：analyze_system_architecture 现在已经是多阶段生成，不需要再并行其他依赖 system_arch 的任务？
        # 其实 database 和 api 设计应该依赖 system_arch 的组件结果，并行可能会导致不一致。
        # 但为了效率，我们先保持并行，后续可以通过 prompt 共享上下文来优化。
        # 更好的做法是串行：先定 System Arch，再定 DB 和 API。
        
        # 1. 先生成系统架构（包含组件和技术栈）
        system_arch = await self.analyze_system_architecture(requirements, selected_proposal)
        
        # 2. 基于确定的组件和需求，设计 DB 和 API
        # 将 system_arch 作为上下文传入（需要修改对应方法签名，或者在 prompt 中注入）
        # 为了最小化改动，暂时还是只传 requirements，但我们可以把 system_arch 的关键信息塞进 requirements 的临时字段里？
        # 或者修改 design_database_schema 签名。
        
        # 让我们修改 design_database_schema 和 design_api_architecture 的签名以接收 system_arch
        database_task = self.design_database_schema(requirements, system_arch)
        api_task = self.design_api_architecture(requirements, system_arch)
        
        database_schema, api_arch = await asyncio.gather(database_task, api_task)
        
        # 整合结果
        architecture_analysis = {
            "selected_proposal": selected_proposal,
            "system_architecture": system_arch,
            "database_design": database_schema,
            "api_architecture": api_arch,
            "technology_stack": system_arch.get("technology_stack", {}),
            "analysis_summary": self._generate_architecture_summary(system_arch, database_schema, api_arch)
        }
        
        logger.info(f"[{self.name}] 架构分析完成")
        return architecture_analysis
    
    def _generate_architecture_summary(self, system_arch: Dict, database_schema: Dict, api_arch: Dict) -> str:
        """生成架构分析总结"""
        return f"""
        系统架构分析完成：
        - 架构模式：{system_arch.get('architecture_pattern', '未知')}
        - 数据库类型：{database_schema.get('database_type', '未知')}
        - API风格：{api_arch.get('api_style', '未知')}
        - 技术栈：{', '.join(system_arch.get('technology_stack', {}).keys())}
        """.strip()
    
    def _generate_default_architecture_analysis(self, requirements: Dict[str, Any] = None) -> Dict[str, Any]:
        """生成默认架构分析"""
        
        # 尝试根据需求推断
        is_web = True
        is_data_heavy = False
        if requirements:
            req_text = str(requirements).lower()
            if "mobile" in req_text or "app" in req_text:
                is_web = False
            if "analysis" in req_text or "report" in req_text or "big data" in req_text:
                is_data_heavy = True
                
        # 基础默认值
        arch_pattern = "微服务架构" if is_web else "客户端-服务器架构"
        frontend = "React/Vue.js" if is_web else "Flutter/React Native"
        backend = "Spring Boot/Django"
        db = "MySQL/PostgreSQL"
        
        if is_data_heavy:
            db += " + ClickHouse/Elasticsearch"
            
        return {
            "architecture_pattern": arch_pattern, # 修复key不匹配
            "technology_stack": {"frontend": frontend, "backend": backend, "database": db},
            "system_components": [{"name": "DefaultService", "description": "默认服务"}], # 修复key不匹配
            "analysis_summary": "默认架构分析（基于简单规则推断）",
            "deployment_architecture": {},
            "performance_considerations": [],
            "scalability_design": [],
            "security_architecture": [],
            "monitoring_architecture": []
        }
    
    def _generate_default_database_design(self, requirements: Dict[str, Any] = None) -> Dict[str, Any]:
        """生成默认数据库设计"""
        
        tables = [
            {
                "name": "users",
                "description": "用户表",
                "fields": ["id", "username", "email", "created_at", "updated_at"]
            }
        ]
        
        # 尝试从需求中提取名词作为表名
        if requirements:
            import re
            functional_reqs = requirements.get('functional_requirements', [])
            req_text = " ".join(functional_reqs)
            # 简单的名词提取（这里仅作示例，实际可以用更复杂的NLP）
            # 提取 "xx管理", "xx系统" 前面的词
            keywords = re.findall(r'(\w+)(?:管理|系统|列表|信息)', req_text)
            seen = set()
            for kw in keywords:
                if len(kw) > 1 and kw not in seen and kw not in ["用户", "系统", "功能"]:
                    seen.add(kw)
                    tables.append({
                        "name": f"{kw}_table", # 简单转义
                        "description": f"{kw}相关数据表",
                        "fields": ["id", "name", "description", "created_at"]
                    })
        
        if len(tables) == 1:
             tables.append({
                "name": "business_data", 
                "description": "核心业务数据表",
                "fields": ["id", "user_id", "data", "status", "created_at"]
            })

        return {
            "database_type": "关系型数据库(MySQL/PostgreSQL)",
            "tables": tables,
            "relationships": "用户表与业务数据表一对多关系",
            "indexing_strategy": "基于查询需求建立索引",
            "optimization_strategy": "查询优化、存储优化",
            "backup_strategy": "定期备份、增量备份"
        }
    
    async def design_api_architecture(self, requirements: Dict[str, Any], system_arch: Dict[str, Any] = None) -> Dict[str, Any]:
        """设计API架构（支持参考系统架构上下文）"""
        logger.info(f"[{self.name}] 开始设计API架构")
        
        functional_reqs = requirements.get('functional_requirements', [])
        
        # 构建系统组件上下文
        component_context = ""
        if system_arch and 'system_components' in system_arch:
            components = system_arch.get('system_components', [])
            component_context = f"""
            【已确定的系统组件】
            以下是系统架构中包含的业务组件，请仅为这些组件设计必要的API接口：
            {json.dumps([c.get('name') for c in components], ensure_ascii=False)}
            """
            
        prompt = f"""
        基于以下功能需求和系统组件，设计API架构方案：
        
        功能需求：
        {chr(10).join(f'- {req}' for req in functional_reqs[:15]) if functional_reqs else '暂无具体功能需求'}
        
        {component_context}
        
        【重要原则】
        1. API设计必须严格对应系统组件，禁止生成无关接口。
        2. 根据系统架构风格（如 RESTful, GraphQL, gRPC）设计接口。
        3. 确保接口命名规范、一致。
        
        请提供详细的API设计方案，包括：
        1. API设计风格（RESTful/GraphQL/gRPC等）
        2. API端点设计
        3. 请求和响应格式
        4. 认证和授权机制
        5. 错误处理机制
        6. API版本管理策略
        7. API文档规范
        8. 性能优化策略
        
        请以JSON格式返回，包含以下字段：
        - api_style: API风格
        - api_endpoints: API端点列表
        - authentication: 认证机制
        - error_handling: 错误处理
        - versioning_strategy: 版本管理
        - performance_optimization: 性能优化
        """
        
        if not getattr(self, "model", None):
            return self._generate_default_api_design(requirements)
        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        
        api_design = self._extract_json(content)
        if not api_design:
            logger.warning(f"[{self.name}] 解析API设计JSON失败，使用默认设计")
            api_design = self._generate_default_api_design(requirements)
        
        return api_design
    
    def _generate_default_api_design(self, requirements: Dict[str, Any] = None) -> Dict[str, Any]:
        """生成默认API设计"""
        
        endpoints = [
            {"path": "/api/v1/users", "method": "GET", "description": "获取用户列表"},
            {"path": "/api/v1/users", "method": "POST", "description": "创建用户"}
        ]
        
        # 尝试从需求生成端点
        if requirements:
            import re
            functional_reqs = requirements.get('functional_requirements', [])
            for req in functional_reqs:
                # 简单匹配动作和资源
                # 例如 "创建订单" -> POST /api/v1/orders
                if "创建" in req or "添加" in req:
                    resource = re.search(r'(?:创建|添加)(\w+)', req)
                    if resource:
                        res_name = resource.group(1)
                        endpoints.append({"path": f"/api/v1/{res_name}s", "method": "POST", "description": req})
                elif "查询" in req or "获取" in req or "搜索" in req:
                    resource = re.search(r'(?:查询|获取|搜索)(\w+)', req)
                    if resource:
                        res_name = resource.group(1)
                        endpoints.append({"path": f"/api/v1/{res_name}s", "method": "GET", "description": req})

        return {
            "api_style": "RESTful API",
            "api_endpoints": endpoints,
            "authentication": "JWT Token",
            "error_handling": "统一错误码和错误信息",
            "versioning_strategy": "URL路径版本控制",
            "performance_optimization": "缓存、分页、限流"
        }
    
    async def _process_model_response(self, response):
        """处理模型响应，支持流式和非流式响应"""
        if hasattr(response, '__aiter__'):
            # 处理流式响应 - 修复重复累积问题
            content_parts = []
            last_content = ""
            
            async for chunk in response:
                current_content = ""
                
                if hasattr(chunk, 'content'):
                    content_value = chunk.content
                    if isinstance(content_value, list):
                        for item in content_value:
                            if isinstance(item, dict) and 'text' in item:
                                current_content += item['text']
                            else:
                                current_content += str(item)
                    else:
                        current_content = str(content_value)
                elif hasattr(chunk, 'text'):
                    current_content = chunk.text
                elif isinstance(chunk, str):
                    current_content = chunk
                else:
                    current_content = str(chunk)
                
                # 检查是否是增量内容，避免重复累积
                if current_content.startswith(last_content):
                    new_content = current_content[len(last_content):]
                    if new_content:
                        content_parts.append(new_content)
                elif current_content != last_content:
                    content_parts.append(current_content)
                
                last_content = current_content
            
            return "".join(content_parts)
        elif hasattr(response, 'text'):
            return response.text
        elif hasattr(response, '__dict__'):
            # 如果是SimpleNamespace或其他对象，优先使用text属性或转换为dict获取text
            if 'text' in response.__dict__:
                return response.__dict__['text']
            else:
                # 如果没有text属性，返回对象的字符串表示
                return str(response)
        else:
            # 如果response没有__dict__属性，尝试其他方法
            if hasattr(response, 'text'):
                return response.text
            else:
                return str(response)
