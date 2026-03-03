"""
关键决策点组件 - 产品经理确认业务决策

设计原则：
1. 人工确认只在关键点 - 产品经理角色，确认业务决策而非技术细节
2. 全部关键点都确认 - 不遗漏任何关键决策
3. 提供默认策略 - 产品经理可快速确认或自定义决策
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import json


class DecisionCategory(Enum):
    """决策类别 - 产品经理需要确认的决策类型"""
    BUSINESS_SCOPE = "business_scope"        # 业务范围：功能是否纳入
    FEATURE_PRIORITY = "feature_priority"    # 功能优先级
    NFR_TARGET = "nfr_target"                # 非功能指标：性能、安全等
    CONSTRAINT = "constraint"                # 项目约束：时间、资源
    RISK_ACCEPTANCE = "risk_acceptance"      # 风险接受


class IssueSeverity(Enum):
    """问题严重程度"""
    BLOCKER = "blocker"      # 阻断性问题，必须解决
    CRITICAL = "critical"    # 严重问题，影响核心功能
    MAJOR = "major"          # 主要问题，影响质量
    MINOR = "minor"          # 次要问题
    SUGGESTION = "suggestion"  # 建议性改进


class IssueCategory(Enum):
    """问题类型"""
    MISSING_FUNCTION = "missing_function"           # 功能缺失
    MISSING_NFR = "missing_nfr"                     # 非功能需求缺失
    INCONSISTENCY = "inconsistency"                 # 需求矛盾
    AMBIGUITY = "ambiguity"                         # 描述模糊
    UNTESTABLE = "untestable"                       # 无法测试
    DUPLICATION = "duplication"                     # 重复需求
    MISSING_CONSTRAINT = "missing_constraint"       # 约束缺失
    TECHNICAL_RISK = "technical_risk"               # 技术风险


@dataclass
class DecisionOption:
    """决策选项"""
    id: str                          # 选项ID
    label: str                       # 显示标签
    impact: str                      # 影响说明
    action: Optional[str] = None     # 执行动作


@dataclass
class KeyDecisionPoint:
    """关键决策点 - 需要产品经理确认"""
    id: str                                    # 决策点ID
    category: DecisionCategory                 # 决策类别
    question: str                              # 决策问题
    context: str                               # 决策背景
    options: List[DecisionOption]              # 可选项列表
    default_option: str                        # 默认选项ID
    selected_option: Optional[str] = None      # 已选选项
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source_issue: Optional[str] = None         # 来源问题ID

    def select(self, option_id: str) -> bool:
        """选择选项"""
        valid_ids = [opt.id for opt in self.options]
        if option_id in valid_ids:
            self.selected_option = option_id
            return True
        return False

    def select_default(self):
        """选择默认选项"""
        self.selected_option = self.default_option

    def get_selected_option(self) -> Optional[DecisionOption]:
        """获取已选选项"""
        if self.selected_option:
            for opt in self.options:
                if opt.id == self.selected_option:
                    return opt
        return None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "category": self.category.value,
            "question": self.question,
            "context": self.context,
            "options": [
                {"id": opt.id, "label": opt.label, "impact": opt.impact}
                for opt in self.options
            ],
            "default_option": self.default_option,
            "selected_option": self.selected_option,
            "created_at": self.created_at,
            "source_issue": self.source_issue
        }


# ============================================================================
# 决策点模板 - 预定义的决策点配置
# ============================================================================

DECISION_TEMPLATES = {
    # 业务范围类 - 功能是否纳入
    "scope_missing_function": {
        "category": DecisionCategory.BUSINESS_SCOPE,
        "question": "是否将缺失的功能纳入需求范围？",
        "options": [
            DecisionOption(
                id="include_high",
                label="纳入（高优先级）",
                impact="增加开发工作量，提升用户体验",
                action="add_function_high"
            ),
            DecisionOption(
                id="include_low",
                label="纳入（低优先级）",
                impact="后续迭代实现",
                action="add_function_low"
            ),
            DecisionOption(
                id="exclude",
                label="不纳入",
                impact="保持当前范围，可能影响用户体验",
                action="exclude_function"
            ),
        ],
        "default_option": "include_low"
    },

    # 非功能指标类 - 性能目标
    "nfr_performance_target": {
        "category": DecisionCategory.NFR_TARGET,
        "question": "请确认性能指标要求",
        "options": [
            DecisionOption(
                id="accept_suggested",
                label="采用建议值",
                impact="明确验收标准",
                action="set_nfr_suggested"
            ),
            DecisionOption(
                id="custom",
                label="自定义指标",
                impact="需要输入具体数值",
                action="set_nfr_custom"
            ),
            DecisionOption(
                id="defer",
                label="暂不量化",
                impact="后续架构设计时确定",
                action="defer_nfr"
            ),
        ],
        "default_option": "accept_suggested"
    },

    # 非功能指标类 - 安全等级
    "nfr_security_level": {
        "category": DecisionCategory.NFR_TARGET,
        "question": "请确认安全等级要求",
        "options": [
            DecisionOption(
                id="high",
                label="高安全等级",
                impact="需要加密存储、审计日志、安全认证",
                action="set_security_high"
            ),
            DecisionOption(
                id="standard",
                label="标准安全等级",
                impact="基本权限控制、操作日志",
                action="set_security_standard"
            ),
            DecisionOption(
                id="basic",
                label="基础安全等级",
                impact="简单认证即可",
                action="set_security_basic"
            ),
        ],
        "default_option": "standard"
    },

    # 项目约束类 - 交付时间
    "constraint_timeline": {
        "category": DecisionCategory.CONSTRAINT,
        "question": "请确认项目时间约束",
        "options": [
            DecisionOption(
                id="accept",
                label="接受建议周期",
                impact="标准开发节奏",
                action="set_timeline_standard"
            ),
            DecisionOption(
                id="urgent",
                label="需要提前交付",
                impact="需要裁剪功能或增加资源",
                action="set_timeline_urgent"
            ),
            DecisionOption(
                id="flexible",
                label="时间灵活",
                impact="可追求更高质量",
                action="set_timeline_flexible"
            ),
        ],
        "default_option": "accept"
    },

    # 项目约束类 - 资源约束
    "constraint_resource": {
        "category": DecisionCategory.CONSTRAINT,
        "question": "请确认开发资源配置",
        "options": [
            DecisionOption(
                id="standard",
                label="标准团队配置",
                impact="按常规团队规模开发",
                action="set_resource_standard"
            ),
            DecisionOption(
                id="minimal",
                label="精简配置",
                impact="需要裁剪功能范围",
                action="set_resource_minimal"
            ),
            DecisionOption(
                id="enhanced",
                label="增强配置",
                impact="可加快交付或提升质量",
                action="set_resource_enhanced"
            ),
        ],
        "default_option": "standard"
    },

    # 风险接受类
    "risk_acceptance": {
        "category": DecisionCategory.RISK_ACCEPTANCE,
        "question": "是否接受该技术风险？",
        "options": [
            DecisionOption(
                id="accept",
                label="接受风险",
                impact="后续制定缓解措施",
                action="accept_risk"
            ),
            DecisionOption(
                id="mitigate",
                label="要求缓解",
                impact="增加技术预研或备选方案",
                action="mitigate_risk"
            ),
            DecisionOption(
                id="avoid",
                label="规避风险",
                impact="调整技术方案或功能范围",
                action="avoid_risk"
            ),
        ],
        "default_option": "accept"
    },

    # 功能优先级类
    "feature_priority": {
        "category": DecisionCategory.FEATURE_PRIORITY,
        "question": "请确认该功能的优先级",
        "options": [
            DecisionOption(
                id="p0",
                label="P0 - 必须",
                impact="本期必须交付",
                action="set_priority_p0"
            ),
            DecisionOption(
                id="p1",
                label="P1 - 重要",
                impact="本期优先交付",
                action="set_priority_p1"
            ),
            DecisionOption(
                id="p2",
                label="P2 - 一般",
                impact="可后续迭代",
                action="set_priority_p2"
            ),
            DecisionOption(
                id="p3",
                label="P3 - 可选",
                impact="视资源情况决定",
                action="set_priority_p3"
            ),
        ],
        "default_option": "p1"
    },
}


# ============================================================================
# 决策点生成器 - 从验证结果生成关键决策点
# ============================================================================

class DecisionPointGenerator:
    """关键决策点生成器"""

    def __init__(self):
        self.templates = DECISION_TEMPLATES
        self.decision_counter = 0

    def generate_from_validation(
        self,
        validation_result: Dict[str, Any],
        requirement_items: Dict[str, Any]
    ) -> List[KeyDecisionPoint]:
        """
        根据验证结果生成关键决策点

        Args:
            validation_result: 验证结果，包含发现的问题列表
            requirement_items: 当前需求项

        Returns:
            关键决策点列表
        """
        decisions = []

        # 1. 从功能缺失生成决策点
        missing_functions = validation_result.get("missing_functions", [])
        for mf in missing_functions:
            if mf.get("severity") in ["blocker", "critical"]:
                decision = self._create_scope_decision(mf)
                if decision:
                    decisions.append(decision)

        # 2. 从非功能缺失生成决策点
        missing_nfrs = validation_result.get("missing_nfrs", [])
        for nfr in missing_nfrs:
            decision = self._create_nfr_decision(nfr)
            if decision:
                decisions.append(decision)

        # 3. 从技术风险生成决策点
        risks = validation_result.get("technical_risks", [])
        for risk in risks:
            if risk.get("severity") in ["blocker", "critical"]:
                decision = self._create_risk_decision(risk)
                if decision:
                    decisions.append(decision)

        # 4. 从约束缺失生成决策点
        constraints = requirement_items.get("constraints")
        if not constraints or (isinstance(constraints, dict) and len(constraints) == 0) or (isinstance(constraints, list) and len(constraints) == 0):
            decision = self._create_constraint_decision()
            if decision:
                decisions.append(decision)

        # 5. 从验证报告的问题列表生成（兼容现有格式）
        issues = validation_result.get("critical_issues", [])
        for issue in issues:
            decision = self._create_decision_from_issue(issue, requirement_items)
            if decision:
                decisions.append(decision)

        return decisions

    def _create_scope_decision(self, missing_feature: Dict) -> Optional[KeyDecisionPoint]:
        """创建业务范围决策点"""
        template = self.templates.get("scope_missing_function")  # 修复：使用正确的模板 key
        if not template:
            return None

        self.decision_counter += 1
        feature_name = missing_feature.get("name", missing_feature.get("description", "未知功能"))
        domain = missing_feature.get("domain", "该类")

        return KeyDecisionPoint(
            id=f"decision_scope_{self.decision_counter:03d}",
            category=template["category"],
            question=template["question"],
            context=f"根据行业分析，「{feature_name}」是{domain}系统的常见功能，当前需求未包含。",
            options=template["options"],
            default_option=template["default_option"],
            source_issue=missing_feature.get("id")
        )

    def _create_nfr_decision(self, missing_nfr: Dict) -> Optional[KeyDecisionPoint]:
        """创建非功能指标决策点"""
        nfr_type = missing_nfr.get("type", "performance")

        # 根据类型选择模板
        if nfr_type in ["security", "auth"]:
            template = self.templates.get("nfr_security_level")
        else:
            template = self.templates.get("nfr_performance_target")

        if not template:
            return None

        self.decision_counter += 1
        current_desc = missing_nfr.get("current_description", "未明确")
        suggested = missing_nfr.get("suggested_metric", "根据行业标准确定")

        return KeyDecisionPoint(
            id=f"decision_nfr_{self.decision_counter:03d}",
            category=template["category"],
            question=template["question"],
            context=f"当前描述为「{current_desc}」，建议量化为：「{suggested}」",
            options=template["options"],
            default_option=template["default_option"],
            source_issue=missing_nfr.get("id")
        )

    def _create_risk_decision(self, risk: Dict) -> Optional[KeyDecisionPoint]:
        """创建风险接受决策点"""
        template = self.templates.get("risk_acceptance")
        if not template:
            return None

        self.decision_counter += 1
        risk_desc = risk.get("description", "未知风险")
        risk_level = risk.get("level", "中")

        return KeyDecisionPoint(
            id=f"decision_risk_{self.decision_counter:03d}",
            category=template["category"],
            question=template["question"],
            context=f"{risk_desc}，风险等级：{risk_level}",
            options=template["options"],
            default_option=template["default_option"],
            source_issue=risk.get("id")
        )

    def _create_constraint_decision(self) -> Optional[KeyDecisionPoint]:
        """创建约束决策点"""
        template = self.templates.get("constraint_timeline")
        if not template:
            return None

        self.decision_counter += 1

        return KeyDecisionPoint(
            id=f"decision_constraint_{self.decision_counter:03d}",
            category=template["category"],
            question=template["question"],
            context="当前需求未明确项目时间约束，建议确认交付周期。",
            options=template["options"],
            default_option=template["default_option"]
        )

    def _create_decision_from_issue(
        self,
        issue: Any,
        requirement_items: Dict
    ) -> Optional[KeyDecisionPoint]:
        """从问题字符串或字典创建决策点（兼容现有格式）"""
        if isinstance(issue, str):
            issue_text = issue
            issue_id = None
        elif isinstance(issue, dict):
            issue_text = issue.get("description", str(issue))
            issue_id = issue.get("id")
        else:
            return None

        # 根据关键词判断问题类型
        issue_lower = issue_text.lower()

        # 功能缺失
        if any(kw in issue_lower for kw in ["缺失", "缺少", "未包含", "遗漏"]):
            self.decision_counter += 1
            return KeyDecisionPoint(
                id=f"decision_issue_{self.decision_counter:03d}",
                category=DecisionCategory.BUSINESS_SCOPE,
                question="是否需要补充该功能？",
                context=issue_text,
                options=self.templates["scope_missing_function"]["options"],
                default_option="include_low",
                source_issue=issue_id
            )

        # 性能/安全指标
        if any(kw in issue_lower for kw in ["性能", "响应", "并发", "吞吐"]):
            self.decision_counter += 1
            return KeyDecisionPoint(
                id=f"decision_issue_{self.decision_counter:03d}",
                category=DecisionCategory.NFR_TARGET,
                question="请确认该非功能需求指标",
                context=issue_text,
                options=self.templates["nfr_performance_target"]["options"],
                default_option="accept_suggested",
                source_issue=issue_id
            )

        # 风险
        if any(kw in issue_lower for kw in ["风险", "不确定", "可能"]):
            self.decision_counter += 1
            return KeyDecisionPoint(
                id=f"decision_issue_{self.decision_counter:03d}",
                category=DecisionCategory.RISK_ACCEPTANCE,
                question="如何处理该风险？",
                context=issue_text,
                options=self.templates["risk_acceptance"]["options"],
                default_option="accept",
                source_issue=issue_id
            )

        return None


# ============================================================================
# 决策确认交互界面
# ============================================================================

class DecisionConfirmUI:
    """决策确认交互界面"""

    def __init__(self, mode: str = "batch"):
        """
        Args:
            mode: 确认模式
                - batch: 批量确认，一次性展示所有决策
                - one_by_one: 逐个确认
        """
        self.mode = mode

    async def confirm(
        self,
        decisions: List[KeyDecisionPoint]
    ) -> List[KeyDecisionPoint]:
        """
        交互式确认决策

        Args:
            decisions: 决策点列表

        Returns:
            确认后的决策点列表
        """
        if not decisions:
            print("无需确认的关键决策点。")
            return decisions

        if self.mode == "batch":
            return await self._batch_confirm(decisions)
        else:
            return await self._one_by_one_confirm(decisions)

    async def _batch_confirm(
        self,
        decisions: List[KeyDecisionPoint]
    ) -> List[KeyDecisionPoint]:
        """批量确认模式"""
        print("\n" + "="*70)
        print(f"【产品经理决策确认】共 {len(decisions)} 个关键点需要确认")
        print("="*70)

        for i, decision in enumerate(decisions):
            print(f"\n{i+1}. [{self._category_label(decision.category)}] {decision.question}")
            print(f"   背景: {decision.context}")
            print(f"   选项:")
            for opt in decision.options:
                default_mark = " [默认]" if opt.id == decision.default_option else ""
                print(f"     [{opt.id}] {opt.label}{default_mark}")
                print(f"         影响: {opt.impact}")

        print("\n" + "-"*70)
        print("输入方式：")
        print("  - 直接回车：全部使用默认策略")
        print("  - 输入编号+选项，如 '1=include_high,3=custom'：指定决策")
        print("  - 输入 'detail'：逐个决策详细确认")
        print("-"*70)

        try:
            user_input = input("\n请确认 (回车使用默认): ").strip().lower()
        except EOFError:
            user_input = ""

        if user_input == "":
            # 使用默认策略
            for decision in decisions:
                decision.select_default()
            print("✓ 已采用全部默认策略")

        elif user_input == "detail":
            # 切换到逐个确认
            return await self._one_by_one_confirm(decisions)

        else:
            # 解析用户指定
            self._parse_user_input(user_input, decisions)

            # 未指定的使用默认
            for decision in decisions:
                if not decision.selected_option:
                    decision.select_default()

        return decisions

    async def _one_by_one_confirm(
        self,
        decisions: List[KeyDecisionPoint]
    ) -> List[KeyDecisionPoint]:
        """逐个确认模式"""

        for i, decision in enumerate(decisions):
            print("\n" + "-"*70)
            print(f"[{i+1}/{len(decisions)}] [{self._category_label(decision.category)}] {decision.question}")
            print(f"背景: {decision.context}")
            print(f"选项:")
            for j, opt in enumerate(decision.options):
                default_mark = " [默认]" if opt.id == decision.default_option else ""
                print(f"  {j+1}. {opt.label}{default_mark}")
                print(f"     影响: {opt.impact}")

            while True:
                try:
                    user_input = input(f"请选择 (1-{len(decision.options)}, 回车默认): ").strip().lower()
                except EOFError:
                    user_input = ""

                if user_input == "":
                    decision.select_default()
                    print(f"✓ 已选择默认: {decision.get_selected_option().label}")
                    break
                else:
                    try:
                        idx = int(user_input) - 1
                        if 0 <= idx < len(decision.options):
                            decision.select(decision.options[idx].id)
                            print(f"✓ 已选择: {decision.get_selected_option().label}")
                            break
                    except ValueError:
                        pass
                    print("输入无效，请重新选择")

        return decisions

    def _parse_user_input(
        self,
        user_input: str,
        decisions: List[KeyDecisionPoint]
    ):
        """解析用户输入"""
        for item in user_input.split(","):
            if "=" in item:
                try:
                    idx_part, opt_part = item.split("=", 1)
                    idx = int(idx_part.strip()) - 1
                    opt_id = opt_part.strip()

                    if 0 <= idx < len(decisions):
                        if decisions[idx].select(opt_id):
                            print(f"✓ 决策{idx+1}: {decisions[idx].get_selected_option().label}")
                        else:
                            print(f"✗ 决策{idx+1}: 无效选项 '{opt_id}'")
                except ValueError:
                    continue

    def _category_label(self, category: DecisionCategory) -> str:
        """获取类别标签"""
        labels = {
            DecisionCategory.BUSINESS_SCOPE: "业务范围",
            DecisionCategory.FEATURE_PRIORITY: "功能优先级",
            DecisionCategory.NFR_TARGET: "非功能指标",
            DecisionCategory.CONSTRAINT: "项目约束",
            DecisionCategory.RISK_ACCEPTANCE: "风险接受",
        }
        return labels.get(category, category.value)


# ============================================================================
# 决策结果应用器
# ============================================================================

class DecisionApplier:
    """决策结果应用器 - 将决策结果应用到需求项"""

    def apply(
        self,
        decisions: List[KeyDecisionPoint],
        requirement_items: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        应用决策结果到需求项

        Args:
            decisions: 已确认的决策点列表
            requirement_items: 当前需求项

        Returns:
            更新后的需求项
        """
        for decision in decisions:
            if not decision.selected_option:
                continue

            action = decision.get_selected_option().action
            if not action:
                continue

            if action.startswith("add_function"):
                priority = "high" if action == "add_function_high" else "medium"
                requirement_items = self._add_function(
                    requirement_items, decision, priority
                )

            elif action == "exclude_function":
                requirement_items = self._exclude_function(
                    requirement_items, decision
                )

            elif action.startswith("set_nfr"):
                requirement_items = self._set_nfr(
                    requirement_items, decision
                )

            elif action.startswith("set_security"):
                level = action.replace("set_security_", "")
                requirement_items = self._set_security_level(
                    requirement_items, level
                )

            elif action.startswith("set_timeline"):
                timeline_type = action.replace("set_timeline_", "")
                requirement_items = self._set_timeline(
                    requirement_items, timeline_type
                )

            elif action.startswith("set_priority"):
                priority = action.replace("set_priority_", "")
                requirement_items = self._set_feature_priority(
                    requirement_items, decision, priority
                )

            elif action == "accept_risk":
                requirement_items = self._accept_risk(
                    requirement_items, decision
                )

            elif action == "mitigate_risk":
                requirement_items = self._mitigate_risk(
                    requirement_items, decision
                )

            elif action == "avoid_risk":
                requirement_items = self._avoid_risk(
                    requirement_items, decision
                )

        return requirement_items

    def _add_function(
        self,
        requirement_items: Dict,
        decision: KeyDecisionPoint,
        priority: str
    ) -> Dict:
        """添加功能到需求"""
        # 从 context 中提取功能名称
        import re
        match = re.search(r"「(.+?)」", decision.context)
        feature_name = match.group(1) if match else f"新功能-{decision.id}"

        # 获取现有功能需求列表
        functional_reqs = requirement_items.get("functional_requirements", [])
        requirement_entries = requirement_items.get("requirement_entries", [])

        # 检查是否已存在
        if feature_name not in functional_reqs:
            functional_reqs.append(feature_name)

        # 添加到需求条目
        new_entry_id = f"FR-{len(requirement_entries)+1:03d}"
        if not any(e.get("description") == feature_name for e in requirement_entries):
            requirement_entries.append({
                "id": new_entry_id,
                "type": "functional",
                "description": feature_name,
                "priority": priority,
                "status": "added",
                "source": "decision",
                "decision_id": decision.id
            })

        requirement_items["functional_requirements"] = functional_reqs
        requirement_items["requirement_entries"] = requirement_entries

        return requirement_items

    def _exclude_function(
        self,
        requirement_items: Dict,
        decision: KeyDecisionPoint
    ) -> Dict:
        """记录排除的功能"""
        if "excluded_features" not in requirement_items:
            requirement_items["excluded_features"] = []

        import re
        match = re.search(r"「(.+?)」", decision.context)
        feature_name = match.group(1) if match else f"功能-{decision.id}"

        requirement_items["excluded_features"].append({
            "name": feature_name,
            "reason": "产品经理决策排除",
            "decision_id": decision.id
        })

        return requirement_items

    def _set_nfr(
        self,
        requirement_items: Dict,
        decision: KeyDecisionPoint
    ) -> Dict:
        """设置非功能需求指标"""
        import re

        # 从 context 中提取建议值
        match = re.search(r"建议量化为：「(.+?)」", decision.context)
        suggested = match.group(1) if match else "根据行业标准确定"

        nfr_reqs = requirement_items.get("non_functional_requirements", [])
        requirement_entries = requirement_items.get("requirement_entries", [])

        # 添加或更新 NFR
        nfr_entry = {
            "id": f"NFR-{len([e for e in requirement_entries if e.get('type') == 'non_functional'])+1:03d}",
            "type": "non_functional",
            "description": suggested,
            "priority": "high",
            "status": "added",
            "source": "decision",
            "decision_id": decision.id
        }

        if suggested not in nfr_reqs:
            nfr_reqs.append(suggested)
            requirement_entries.append(nfr_entry)

        requirement_items["non_functional_requirements"] = nfr_reqs
        requirement_items["requirement_entries"] = requirement_entries

        return requirement_items

    def _set_security_level(
        self,
        requirement_items: Dict,
        level: str
    ) -> Dict:
        """设置安全等级"""
        security_levels = {
            "high": {
                "requirements": [
                    "数据加密存储",
                    "完整的审计日志",
                    "多因素认证",
                    "安全扫描通过"
                ],
                "description": "高安全等级"
            },
            "standard": {
                "requirements": [
                    "基于RBAC的权限控制",
                    "操作日志记录",
                    "密码加密存储"
                ],
                "description": "标准安全等级"
            },
            "basic": {
                "requirements": [
                    "基础用户认证",
                    "简单权限控制"
                ],
                "description": "基础安全等级"
            }
        }

        level_config = security_levels.get(level, security_levels["standard"])

        requirement_items["security_level"] = level
        requirement_items["security_requirements"] = level_config["requirements"]

        # 添加到 NFR
        nfr_reqs = requirement_items.get("non_functional_requirements", [])
        for req in level_config["requirements"]:
            if req not in nfr_reqs:
                nfr_reqs.append(req)

        requirement_items["non_functional_requirements"] = nfr_reqs

        return requirement_items

    def _set_timeline(
        self,
        requirement_items: Dict,
        timeline_type: str
    ) -> Dict:
        """设置项目时间约束"""
        timeline_configs = {
            "standard": {"weeks": 12, "description": "标准开发周期"},
            "urgent": {"weeks": 6, "description": "紧急交付"},
            "flexible": {"weeks": 16, "description": "灵活时间"}
        }

        config = timeline_configs.get(timeline_type, timeline_configs["standard"])

        if "constraints" not in requirement_items:
            requirement_items["constraints"] = {}

        requirement_items["constraints"]["timeline"] = {
            "type": timeline_type,
            "weeks": config["weeks"],
            "description": config["description"]
        }

        return requirement_items

    def _set_feature_priority(
        self,
        requirement_items: Dict,
        decision: KeyDecisionPoint,
        priority: str
    ) -> Dict:
        """设置功能优先级"""
        if "feature_priorities" not in requirement_items:
            requirement_items["feature_priorities"] = {}

        requirement_items["feature_priorities"][decision.id] = priority

        return requirement_items

    def _accept_risk(
        self,
        requirement_items: Dict,
        decision: KeyDecisionPoint
    ) -> Dict:
        """接受风险"""
        if "accepted_risks" not in requirement_items:
            requirement_items["accepted_risks"] = []

        requirement_items["accepted_risks"].append({
            "description": decision.context,
            "decision_id": decision.id,
            "action": "accepted"
        })

        return requirement_items

    def _mitigate_risk(
        self,
        requirement_items: Dict,
        decision: KeyDecisionPoint
    ) -> Dict:
        """缓解风险 - 添加缓解措施需求"""
        if "risk_mitigations" not in requirement_items:
            requirement_items["risk_mitigations"] = []

        requirement_items["risk_mitigations"].append({
            "description": decision.context,
            "decision_id": decision.id,
            "action": "mitigate",
            "requirement": "需要技术预研或备选方案"
        })

        # 添加缓解需求到功能需求
        functional_reqs = requirement_items.get("functional_requirements", [])
        functional_reqs.append(f"风险缓解: {decision.context[:50]}...")
        requirement_items["functional_requirements"] = functional_reqs

        return requirement_items

    def _avoid_risk(
        self,
        requirement_items: Dict,
        decision: KeyDecisionPoint
    ) -> Dict:
        """规避风险 - 记录需要调整的内容"""
        if "avoided_risks" not in requirement_items:
            requirement_items["avoided_risks"] = []

        requirement_items["avoided_risks"].append({
            "description": decision.context,
            "decision_id": decision.id,
            "action": "avoid",
            "note": "需要调整技术方案或功能范围"
        })

        return requirement_items


# ============================================================================
# 决策报告生成器
# ============================================================================

class DecisionReportGenerator:
    """决策报告生成器"""

    def generate_markdown(
        self,
        decisions: List[KeyDecisionPoint]
    ) -> str:
        """生成 Markdown 格式的决策报告"""
        lines = [
            "# 产品经理决策报告",
            f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\n共 {len(decisions)} 个关键决策点\n"
        ]

        # 按类别分组
        by_category = {}
        for decision in decisions:
            cat = decision.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(decision)

        category_labels = {
            "business_scope": "业务范围",
            "feature_priority": "功能优先级",
            "nfr_target": "非功能指标",
            "constraint": "项目约束",
            "risk_acceptance": "风险接受",
        }

        for cat, cat_decisions in by_category.items():
            lines.append(f"\n## {category_labels.get(cat, cat)}\n")
            lines.append("| 决策 | 背景 | 选择 | 影响 |")
            lines.append("|------|------|------|------|")

            for d in cat_decisions:
                selected = d.get_selected_option()
                lines.append(
                    f"| {d.question} | {d.context[:30]}... | "
                    f"{selected.label if selected else '-'} | "
                    f"{selected.impact if selected else '-'} |"
                )

        # 决策摘要
        lines.append("\n## 决策摘要\n")
        for decision in decisions:
            selected = decision.get_selected_option()
            lines.append(f"- **{decision.id}**: {decision.question}")
            lines.append(f"  - 选择: {selected.label if selected else '未选择'}")
            lines.append(f"  - 影响: {selected.impact if selected else '-'}\n")

        return "\n".join(lines)

    def generate_json(
        self,
        decisions: List[KeyDecisionPoint]
    ) -> str:
        """生成 JSON 格式的决策报告"""
        return json.dumps(
            [d.to_dict() for d in decisions],
            ensure_ascii=False,
            indent=2
        )
