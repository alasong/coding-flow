"""
关键决策点组件单元测试
"""

import pytest
import asyncio
from agents.key_decision_point import (
    DecisionCategory,
    IssueSeverity,
    IssueCategory,
    DecisionOption,
    KeyDecisionPoint,
    DecisionPointGenerator,
    DecisionConfirmUI,
    DecisionApplier,
    DecisionReportGenerator,
    DECISION_TEMPLATES,
)


class TestDecisionOption:
    """DecisionOption 测试"""

    def test_create_option(self):
        """测试创建决策选项"""
        option = DecisionOption(
            id="test_id",
            label="测试选项",
            impact="测试影响",
            action="test_action"
        )
        assert option.id == "test_id"
        assert option.label == "测试选项"
        assert option.impact == "测试影响"
        assert option.action == "test_action"


class TestKeyDecisionPoint:
    """KeyDecisionPoint 测试"""

    def test_create_decision_point(self):
        """测试创建决策点"""
        options = [
            DecisionOption(id="opt1", label="选项1", impact="影响1"),
            DecisionOption(id="opt2", label="选项2", impact="影响2"),
        ]

        decision = KeyDecisionPoint(
            id="test_001",
            category=DecisionCategory.BUSINESS_SCOPE,
            question="测试问题？",
            context="测试背景",
            options=options,
            default_option="opt1"
        )

        assert decision.id == "test_001"
        assert decision.category == DecisionCategory.BUSINESS_SCOPE
        assert decision.question == "测试问题？"
        assert len(decision.options) == 2
        assert decision.default_option == "opt1"
        assert decision.selected_option is None

    def test_select_option(self):
        """测试选择选项"""
        options = [
            DecisionOption(id="opt1", label="选项1", impact="影响1"),
            DecisionOption(id="opt2", label="选项2", impact="影响2"),
        ]

        decision = KeyDecisionPoint(
            id="test_001",
            category=DecisionCategory.BUSINESS_SCOPE,
            question="测试问题？",
            context="测试背景",
            options=options,
            default_option="opt1"
        )

        # 选择有效选项
        result = decision.select("opt2")
        assert result is True
        assert decision.selected_option == "opt2"

        # 选择无效选项
        result = decision.select("invalid")
        assert result is False
        assert decision.selected_option == "opt2"  # 保持原选择

    def test_select_default(self):
        """测试选择默认选项"""
        options = [
            DecisionOption(id="opt1", label="选项1", impact="影响1"),
            DecisionOption(id="opt2", label="选项2", impact="影响2"),
        ]

        decision = KeyDecisionPoint(
            id="test_001",
            category=DecisionCategory.BUSINESS_SCOPE,
            question="测试问题？",
            context="测试背景",
            options=options,
            default_option="opt1"
        )

        decision.select_default()
        assert decision.selected_option == "opt1"

    def test_get_selected_option(self):
        """测试获取已选选项"""
        options = [
            DecisionOption(id="opt1", label="选项1", impact="影响1"),
            DecisionOption(id="opt2", label="选项2", impact="影响2"),
        ]

        decision = KeyDecisionPoint(
            id="test_001",
            category=DecisionCategory.BUSINESS_SCOPE,
            question="测试问题？",
            context="测试背景",
            options=options,
            default_option="opt1"
        )

        # 未选择时返回 None
        assert decision.get_selected_option() is None

        # 选择后返回选项对象
        decision.select("opt2")
        selected = decision.get_selected_option()
        assert selected is not None
        assert selected.id == "opt2"
        assert selected.label == "选项2"

    def test_to_dict(self):
        """测试转换为字典"""
        options = [
            DecisionOption(id="opt1", label="选项1", impact="影响1"),
        ]

        decision = KeyDecisionPoint(
            id="test_001",
            category=DecisionCategory.BUSINESS_SCOPE,
            question="测试问题？",
            context="测试背景",
            options=options,
            default_option="opt1"
        )

        d = decision.to_dict()
        assert d["id"] == "test_001"
        assert d["category"] == "business_scope"
        assert d["question"] == "测试问题？"
        assert len(d["options"]) == 1


class TestDecisionPointGenerator:
    """DecisionPointGenerator 测试"""

    def setup_method(self):
        self.generator = DecisionPointGenerator()

    def test_templates_exist(self):
        """测试模板存在"""
        assert "scope_missing_function" in DECISION_TEMPLATES
        assert "nfr_performance_target" in DECISION_TEMPLATES
        assert "risk_acceptance" in DECISION_TEMPLATES

    def test_generate_from_missing_functions(self):
        """测试从功能缺失生成决策点"""
        validation_result = {
            "missing_functions": [
                {
                    "id": "mf_001",
                    "name": "文档分类",
                    "domain": "文档管理",
                    "severity": "critical"
                }
            ]
        }

        # 提供空的 constraints 以避免额外生成约束决策点
        requirement_items = {"constraints": {"timeline": {"weeks": 12}}}

        decisions = self.generator.generate_from_validation(
            validation_result, requirement_items
        )

        assert len(decisions) == 1
        assert decisions[0].category == DecisionCategory.BUSINESS_SCOPE
        assert "文档分类" in decisions[0].context

    def test_generate_from_missing_nfrs(self):
        """测试从非功能缺失生成决策点"""
        validation_result = {
            "missing_nfrs": [
                {
                    "id": "nfr_001",
                    "type": "performance",
                    "current_description": "高性能",
                    "suggested_metric": "响应时间≤2秒"
                }
            ]
        }

        # 提供空的 constraints 以避免额外生成约束决策点
        requirement_items = {"constraints": {"timeline": {"weeks": 12}}}

        decisions = self.generator.generate_from_validation(
            validation_result, requirement_items
        )

        assert len(decisions) == 1
        assert decisions[0].category == DecisionCategory.NFR_TARGET

    def test_generate_from_risks(self):
        """测试从技术风险生成决策点"""
        validation_result = {
            "technical_risks": [
                {
                    "id": "risk_001",
                    "description": "全文检索性能风险",
                    "level": "高",
                    "severity": "critical"
                }
            ]
        }

        # 提供空的 constraints 以避免额外生成约束决策点
        requirement_items = {"constraints": {"timeline": {"weeks": 12}}}

        decisions = self.generator.generate_from_validation(
            validation_result, requirement_items
        )

        assert len(decisions) == 1
        assert decisions[0].category == DecisionCategory.RISK_ACCEPTANCE

    def test_generate_from_constraints_missing(self):
        """测试约束缺失时生成决策点"""
        validation_result = {}
        requirement_items = {"constraints": []}

        decisions = self.generator.generate_from_validation(
            validation_result, requirement_items
        )

        # 应该生成一个约束决策点
        assert any(d.category == DecisionCategory.CONSTRAINT for d in decisions)

    def test_generate_from_issue_strings(self):
        """测试从问题字符串生成决策点（兼容现有格式）"""
        validation_result = {
            "critical_issues": [
                "缺失文档分类功能",
                "性能指标未明确",
                "存在技术风险"
            ]
        }

        decisions = self.generator.generate_from_validation(
            validation_result, {}
        )

        assert len(decisions) >= 1

    def test_skip_non_critical_issues(self):
        """测试跳过非关键问题"""
        validation_result = {
            "missing_functions": [
                {
                    "id": "mf_001",
                    "name": "次要功能",
                    "severity": "minor"  # 非关键
                }
            ]
        }

        # 提供有效的 constraints 以避免额外生成约束决策点
        requirement_items = {"constraints": {"timeline": {"weeks": 12}}}

        decisions = self.generator.generate_from_validation(
            validation_result, requirement_items
        )

        # 非关键问题不应生成决策点
        assert len(decisions) == 0


class TestDecisionApplier:
    """DecisionApplier 测试"""

    def setup_method(self):
        self.applier = DecisionApplier()

    def test_apply_add_function(self):
        """测试添加功能决策"""
        options = DECISION_TEMPLATES["scope_missing_function"]["options"]

        decision = KeyDecisionPoint(
            id="test_001",
            category=DecisionCategory.BUSINESS_SCOPE,
            question="是否纳入？",
            context="根据分析，「文档分类」是常见功能",
            options=options,
            default_option="include_low"
        )
        decision.select("include_high")

        requirement_items = {
            "functional_requirements": [],
            "requirement_entries": []
        }

        result = self.applier.apply([decision], requirement_items)

        assert "文档分类" in result["functional_requirements"]
        assert len(result["requirement_entries"]) == 1
        assert result["requirement_entries"][0]["priority"] == "high"

    def test_apply_exclude_function(self):
        """测试排除功能决策"""
        options = DECISION_TEMPLATES["scope_missing_function"]["options"]

        decision = KeyDecisionPoint(
            id="test_001",
            category=DecisionCategory.BUSINESS_SCOPE,
            question="是否纳入？",
            context="根据分析，「文档分类」是常见功能",
            options=options,
            default_option="include_low"
        )
        decision.select("exclude")

        requirement_items = {}

        result = self.applier.apply([decision], requirement_items)

        assert "excluded_features" in result
        assert len(result["excluded_features"]) == 1

    def test_apply_set_nfr(self):
        """测试设置非功能指标"""
        options = DECISION_TEMPLATES["nfr_performance_target"]["options"]

        decision = KeyDecisionPoint(
            id="test_001",
            category=DecisionCategory.NFR_TARGET,
            question="确认性能指标？",
            context="当前为「高性能」，建议量化为：「响应时间≤2秒」",
            options=options,
            default_option="accept_suggested"
        )
        decision.select("accept_suggested")

        requirement_items = {
            "non_functional_requirements": [],
            "requirement_entries": []
        }

        result = self.applier.apply([decision], requirement_items)

        assert "响应时间≤2秒" in result["non_functional_requirements"]

    def test_apply_set_security_level(self):
        """测试设置安全等级"""
        options = DECISION_TEMPLATES["nfr_security_level"]["options"]

        decision = KeyDecisionPoint(
            id="test_001",
            category=DecisionCategory.NFR_TARGET,
            question="确认安全等级？",
            context="请确认安全等级",
            options=options,
            default_option="standard"
        )
        decision.select("high")

        requirement_items = {
            "non_functional_requirements": []
        }

        result = self.applier.apply([decision], requirement_items)

        assert result["security_level"] == "high"
        assert "数据加密存储" in result["security_requirements"]

    def test_apply_set_timeline(self):
        """测试设置时间约束"""
        options = DECISION_TEMPLATES["constraint_timeline"]["options"]

        decision = KeyDecisionPoint(
            id="test_001",
            category=DecisionCategory.CONSTRAINT,
            question="确认时间约束？",
            context="建议交付周期",
            options=options,
            default_option="accept"
        )
        decision.select("urgent")

        requirement_items = {}

        result = self.applier.apply([decision], requirement_items)

        assert "constraints" in result
        assert result["constraints"]["timeline"]["type"] == "urgent"
        assert result["constraints"]["timeline"]["weeks"] == 6

    def test_apply_accept_risk(self):
        """测试接受风险"""
        options = DECISION_TEMPLATES["risk_acceptance"]["options"]

        decision = KeyDecisionPoint(
            id="test_001",
            category=DecisionCategory.RISK_ACCEPTANCE,
            question="是否接受风险？",
            context="全文检索性能风险，风险等级：高",
            options=options,
            default_option="accept"
        )
        decision.select("accept")

        requirement_items = {}

        result = self.applier.apply([decision], requirement_items)

        assert "accepted_risks" in result
        assert len(result["accepted_risks"]) == 1

    def test_apply_mitigate_risk(self):
        """测试缓解风险"""
        options = DECISION_TEMPLATES["risk_acceptance"]["options"]

        decision = KeyDecisionPoint(
            id="test_001",
            category=DecisionCategory.RISK_ACCEPTANCE,
            question="是否接受风险？",
            context="全文检索性能风险，风险等级：高",
            options=options,
            default_option="accept"
        )
        decision.select("mitigate")

        requirement_items = {
            "functional_requirements": []
        }

        result = self.applier.apply([decision], requirement_items)

        assert "risk_mitigations" in result
        assert len(result["risk_mitigations"]) == 1


class TestDecisionReportGenerator:
    """DecisionReportGenerator 测试"""

    def setup_method(self):
        self.generator = DecisionReportGenerator()

    def test_generate_markdown(self):
        """测试生成 Markdown 报告"""
        options = DECISION_TEMPLATES["scope_missing_function"]["options"]

        decision = KeyDecisionPoint(
            id="test_001",
            category=DecisionCategory.BUSINESS_SCOPE,
            question="是否纳入？",
            context="根据分析，「文档分类」是常见功能",
            options=options,
            default_option="include_low"
        )
        decision.select("include_high")

        report = self.generator.generate_markdown([decision])

        assert "# 产品经理决策报告" in report
        assert "业务范围" in report
        assert "是否纳入？" in report

    def test_generate_json(self):
        """测试生成 JSON 报告"""
        options = DECISION_TEMPLATES["scope_missing_function"]["options"]

        decision = KeyDecisionPoint(
            id="test_001",
            category=DecisionCategory.BUSINESS_SCOPE,
            question="是否纳入？",
            context="测试背景",
            options=options,
            default_option="include_low"
        )
        decision.select("include_high")

        report = self.generator.generate_json([decision])

        assert '"id": "test_001"' in report
        assert '"category": "business_scope"' in report


class TestDecisionConfirmUI:
    """DecisionConfirmUI 测试"""

    def test_batch_confirm_default(self, monkeypatch):
        """测试批量确认使用默认策略"""
        ui = DecisionConfirmUI(mode="batch")

        options = DECISION_TEMPLATES["scope_missing_function"]["options"]
        decision = KeyDecisionPoint(
            id="test_001",
            category=DecisionCategory.BUSINESS_SCOPE,
            question="是否纳入？",
            context="测试背景",
            options=options,
            default_option="include_low"
        )

        # 模拟用户输入回车
        monkeypatch.setattr('builtins.input', lambda _: "")

        async def run_test():
            result = await ui.confirm([decision])
            assert result[0].selected_option == "include_low"

        asyncio.run(run_test())

    def test_one_by_one_confirm(self, monkeypatch):
        """测试逐个确认"""
        ui = DecisionConfirmUI(mode="one_by_one")

        options = DECISION_TEMPLATES["scope_missing_function"]["options"]
        decision = KeyDecisionPoint(
            id="test_001",
            category=DecisionCategory.BUSINESS_SCOPE,
            question="是否纳入？",
            context="测试背景",
            options=options,
            default_option="include_low"
        )

        # 模拟用户输入 3（选择第三个选项 "exclude"）
        monkeypatch.setattr('builtins.input', lambda _: "3")

        async def run_test():
            result = await ui.confirm([decision])
            assert result[0].selected_option == "exclude"

        asyncio.run(run_test())


class TestIntegration:
    """集成测试"""

    def test_full_workflow(self):
        """测试完整工作流"""
        # 1. 生成器
        generator = DecisionPointGenerator()

        validation_result = {
            "missing_functions": [
                {
                    "id": "mf_001",
                    "name": "文档分类",
                    "domain": "文档管理",
                    "severity": "critical"
                }
            ],
            "missing_nfrs": [
                {
                    "id": "nfr_001",
                    "type": "performance",
                    "current_description": "高性能",
                    "suggested_metric": "响应时间≤2秒"
                }
            ],
            "technical_risks": [
                {
                    "id": "risk_001",
                    "description": "全文检索性能风险",
                    "level": "中",
                    "severity": "critical"
                }
            ]
        }

        # 提供有效的 constraints 以避免额外生成约束决策点
        requirement_items = {
            "functional_requirements": [],
            "non_functional_requirements": [],
            "requirement_entries": [],
            "constraints": {"timeline": {"weeks": 12}}
        }

        decisions = generator.generate_from_validation(validation_result, requirement_items)

        assert len(decisions) == 3

        # 2. 选择默认策略
        for decision in decisions:
            decision.select_default()

        # 3. 应用决策
        applier = DecisionApplier()

        result = applier.apply(decisions, requirement_items)

        assert "文档分类" in result["functional_requirements"]
        assert "响应时间≤2秒" in result["non_functional_requirements"]
        assert "accepted_risks" in result

        # 4. 生成报告
        report_gen = DecisionReportGenerator()
        report = report_gen.generate_markdown(decisions)

        assert "产品经理决策报告" in report
        assert "文档分类" in report or "非功能指标" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
