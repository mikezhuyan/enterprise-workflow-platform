"""
审批节点配置示例

本文件展示如何在实际工作流中使用审批节点
"""

# 示例1: 简单的用户审批节点配置
APPROVAL_NODE_USER = {
    "id": "approval_1",
    "type": "approval",
    "position": {"x": 300, "y": 200},
    "data": {
        "label": "经理审批",
        "assignee_type": "user",  # user, role, department
        "assignee_id": "user_uuid_here",  # 用户的UUID
        "timeout": 86400,  # 超时时间(秒)，默认24小时
        "auto_action": "reject"  # 超时自动操作: approve, reject
    }
}

# 示例2: 角色审批（指定角色中的任意成员可审批）
APPROVAL_NODE_ROLE = {
    "id": "approval_2",
    "type": "approval",
    "position": {"x": 500, "y": 300},
    "data": {
        "label": "财务审批",
        "assignee_type": "role",  # role - 指定角色的所有成员都可以审批
        "assignee_id": "role_uuid_here",  # 角色的UUID
        "timeout": 172800,  # 48小时
        "auto_action": "reject"
    }
}

# 示例3: 部门审批（指定部门的成员可审批）
APPROVAL_NODE_DEPARTMENT = {
    "id": "approval_3",
    "type": "approval",
    "position": {"x": 700, "y": 400},
    "data": {
        "label": "部门主管审批",
        "assignee_type": "department",  # department
        "assignee_id": "department_uuid_here",  # 部门的UUID
        "timeout": 43200,  # 12小时
        "auto_action": "approve"  # 超时自动通过
    }
}

# 示例4: 完整的工作流定义（包含审批节点）
WORKFLOW_WITH_APPROVAL = {
    "id": "workflow_1",
    "name": "请假审批流程",
    "nodes": [
        {
            "id": "start",
            "type": "start",
            "position": {"x": 100, "y": 200},
            "data": {"label": "开始"}
        },
        {
            "id": "approval_manager",
            "type": "approval",
            "position": {"x": 300, "y": 200},
            "data": {
                "label": "直属经理审批",
                "assignee_type": "user",
                "assignee_id": "manager_uuid",
                "timeout": 86400,
                "auto_action": "reject"
            }
        },
        {
            "id": "condition_days",
            "type": "condition",
            "position": {"x": 500, "y": 200},
            "data": {
                "label": "请假天数>3天?",
                "conditions": [
                    {
                        "expression": "input.days > 3",
                        "target": "approval_hr"
                    }
                ]
            }
        },
        {
            "id": "approval_hr",
            "type": "approval",
            "position": {"x": 500, "y": 400},
            "data": {
                "label": "HR审批",
                "assignee_type": "role",
                "assignee_id": "hr_role_uuid",
                "timeout": 172800,
                "auto_action": "reject"
            }
        },
        {
            "id": "end",
            "type": "end",
            "position": {"x": 700, "y": 200},
            "data": {"label": "结束"}
        }
    ],
    "edges": [
        {"id": "e1", "source": "start", "target": "approval_manager"},
        {"id": "e2", "source": "approval_manager", "target": "condition_days"},
        {"id": "e3", "source": "condition_days", "target": "end"},
        {"id": "e4", "source": "condition_days", "target": "approval_hr"},
        {"id": "e5", "source": "approval_hr", "target": "end"}
    ]
}


"""
使用说明:

1. 创建包含审批节点的工作流后，执行工作流时:
   - 审批节点会暂停工作流执行
   - 系统自动创建审批任务记录
   - 审批任务可在上下文中通过 _approval_pending 变量获取

2. 审批API使用:
   
   # 获取待审批列表
   GET /api/v1/approvals/pending
   
   # 获取审批详情
   GET /api/v1/approvals/{approval_id}
   
   # 审批通过
   POST /api/v1/approvals/{approval_id}/approve
   Body: {"comment": "同意"}
   
   # 审批拒绝
   POST /api/v1/approvals/{approval_id}/reject
   Body: {"comment": "不符合要求"}
   
   # 转办
   POST /api/v1/approvals/{approval_id}/transfer
   Body: {"new_assignee_id": "user_uuid", "comment": "请协助审批"}

3. 审批完成后，需要调用工作流引擎的接口继续执行工作流
   （此功能需要在 WorkflowEngine 中实现支持暂停/恢复执行）
"""
