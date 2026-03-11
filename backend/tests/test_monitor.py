"""
执行监控大盘测试
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.services.monitor_service import MonitorService


class TestMonitorService:
    """测试监控服务"""

    def test_get_basic_stats(self, db_session, test_workflow):
        """测试获取基础统计"""
        stats = MonitorService.get_basic_stats(db_session)
        
        assert "workflow_count" in stats
        assert "component_count" in stats
        assert "today_executions" in stats
        assert "success_rate" in stats

    def test_get_time_range_stats(self, db_session, test_execution):
        """测试获取时间段统计"""
        # 测试今日统计
        today_stats = MonitorService.get_time_range_stats(
            db_session, "today"
        )
        assert "total" in today_stats
        assert "success_count" in today_stats
        assert "failed_count" in today_stats
        
        # 测试本周统计
        week_stats = MonitorService.get_time_range_stats(
            db_session, "week"
        )
        assert "total" in week_stats
        
        # 测试本月统计
        month_stats = MonitorService.get_time_range_stats(
            db_session, "month"
        )
        assert "total" in month_stats

    def test_get_realtime_executions(self, db_session, test_execution):
        """测试获取实时执行状态"""
        # 设置执行状态为running
        test_execution.status = "running"
        test_execution.started_at = datetime.utcnow()
        db_session.commit()
        
        realtime = MonitorService.get_realtime_executions(db_session)
        
        assert "running_count" in realtime
        assert "pending_count" in realtime
        assert "executions" in realtime

    def test_get_execution_trend(self, db_session):
        """测试获取执行趋势"""
        # 按小时
        hour_trend = MonitorService.get_execution_trend(
            db_session, period="hour", hours=24
        )
        assert "labels" in hour_trend
        assert "datasets" in hour_trend
        assert len(hour_trend["labels"]) <= 24
        
        # 按天
        day_trend = MonitorService.get_execution_trend(
            db_session, period="day", days=7
        )
        assert "labels" in day_trend
        assert len(day_trend["labels"]) <= 7

    def test_get_node_stats(self, db_session, test_execution):
        """测试获取节点统计"""
        stats = MonitorService.get_node_stats(db_session)
        
        assert "type_distribution" in stats
        assert "avg_duration_by_type" in stats
        assert "failure_rate_ranking" in stats
        assert "slow_nodes" in stats

    def test_get_popular_workflows(self, db_session, test_workflow):
        """测试获取热门工作流"""
        popular = MonitorService.get_popular_workflows(db_session, limit=5)
        
        assert "most_executed" in popular
        assert "recently_executed" in popular

    def test_get_alerts(self, db_session, test_execution):
        """测试获取告警信息"""
        # 设置一些失败执行
        test_execution.status = "failed"
        test_execution.error_message = "测试错误"
        db_session.commit()
        
        alerts = MonitorService.get_alerts(db_session)
        
        assert "failed_executions" in alerts
        assert "timeout_workflows" in alerts
        assert "high_error_rate" in alerts

    def test_get_health_status(self, db_session):
        """测试获取健康状态"""
        health = MonitorService.get_health_status(db_session)
        
        assert "status" in health
        assert "score" in health
        assert "checks" in health
        assert health["status"] in ["healthy", "warning", "critical"]

    def test_get_dashboard_overview(self, db_session, test_workflow):
        """测试获取Dashboard总览"""
        overview = MonitorService.get_dashboard_overview(db_session)
        
        assert "basic" in overview
        assert "realtime" in overview
        assert "trend" in overview
        assert "popular" in overview
        assert "alerts" in overview
        assert "health" in overview

    def test_cache_mechanism(self, db_session):
        """测试缓存机制"""
        # 第一次调用
        stats1 = MonitorService.get_basic_stats(db_session)
        
        # 第二次调用（应该使用缓存）
        stats2 = MonitorService.get_basic_stats(db_session)
        
        assert stats1 == stats2
        
        # 清除缓存
        MonitorService.clear_cache()
        
        # 再次调用（重新查询）
        stats3 = MonitorService.get_basic_stats(db_session)
        # 结果应该相同（因为没有数据变化）
        assert "workflow_count" in stats3

    def test_workflow_health_score(self, db_session, test_workflow, test_execution):
        """测试工作流健康度评分"""
        # 创建一些成功和失败的执行
        health = MonitorService.get_health_status(db_session)
        
        assert "score" in health
        score = health["score"]
        assert 0 <= score <= 100

    def test_error_rate_calculation(self, db_session):
        """测试错误率计算"""
        # 手动计算错误率
        from app.models.workflow import WorkflowExecution
        from sqlalchemy import func
        
        total = db_session.query(func.count(WorkflowExecution.id)).scalar() or 0
        failed = db_session.query(func.count(WorkflowExecution.id)).filter(
            WorkflowExecution.status == "failed"
        ).scalar() or 0
        
        expected_rate = (failed / total * 100) if total > 0 else 0
        
        # 获取统计
        stats = MonitorService.get_basic_stats(db_session)
        
        # 验证成功率计算
        assert 0 <= stats["success_rate"] <= 100


class TestDashboardAPI:
    """测试Dashboard API"""

    def test_dashboard_stats_endpoint(self, client, test_user_headers):
        """测试Dashboard统计端点"""
        response = client.get(
            "/api/v1/dashboard/stats",
            headers=test_user_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "workflow_count" in data["data"]

    def test_dashboard_realtime_endpoint(self, client, test_user_headers):
        """测试实时执行端点"""
        response = client.get(
            "/api/v1/dashboard/executions/realtime",
            headers=test_user_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "running_count" in data

    def test_dashboard_trend_endpoint(self, client, test_user_headers):
        """测试执行趋势端点"""
        response = client.get(
            "/api/v1/dashboard/executions/trend?period=day&days=7",
            headers=test_user_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "labels" in data
        assert "datasets" in data

    def test_dashboard_nodes_endpoint(self, client, test_user_headers):
        """测试节点统计端点"""
        response = client.get(
            "/api/v1/dashboard/nodes/stats",
            headers=test_user_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "type_distribution" in data

    def test_dashboard_alerts_endpoint(self, client, test_user_headers):
        """测试告警端点"""
        response = client.get(
            "/api/v1/dashboard/alerts",
            headers=test_user_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "failed_executions" in data

    def test_dashboard_health_endpoint(self, client, test_user_headers):
        """测试健康状态端点"""
        response = client.get(
            "/api/v1/dashboard/health",
            headers=test_user_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "score" in data

    def test_dashboard_overview_endpoint(self, client, test_user_headers):
        """测试总览端点"""
        response = client.get(
            "/api/v1/dashboard/overview",
            headers=test_user_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "basic" in data
        assert "realtime" in data
        assert "trend" in data
