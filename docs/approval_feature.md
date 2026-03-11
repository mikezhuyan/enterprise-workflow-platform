# 审批流程节点功能文档

## 功能概述

审批流程节点是工作流引擎的重要组成部分，允许在工作流执行过程中插入人工审批环节。支持多种指派方式（用户、角色、部门），以及通过/拒绝/转办等操作。

## 实现内容

### 1. 工作流引擎 (backend/app/workflow/engine.py)

- **NodeType.APPROVAL**: 新增的审批节点类型
- **_handle_approval**: 审批节点处理器，负责：
  - 创建审批任务信息
  - 将任务信息保存到执行上下文
  - 返回待审批状态

### 2. 数据模型 (backend/app/models/workflow.py)

**ApprovalTask 表结构:**

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 主键 |
| execution_id | UUID | 工作流执行ID |
| node_id | str | 节点ID |
| node_name | str | 节点名称 |
| status | str | 状态: pending/approved/rejected/transferred |
| assignee_type | str | 指派类型: user/role/department |
| assignee_id | UUID | 指派人/角色/部门ID |
| comment | str | 审批意见 |
| completed_by | UUID | 完成人 |
| completed_at | datetime | 完成时间 |
| timeout_at | datetime | 超时时间 |
| auto_action | str | 超时自动操作: approve/reject |
| input_data | JSON | 输入数据 |
| output_data | JSON | 输出数据 |

### 3. API端点 (backend/app/api/v1/endpoints/approvals.py)

#### 获取待审批列表
```
GET /api/v1/approvals/pending?page=1&page_size=20
Authorization: Bearer {token}
```

响应示例:
```json
{
  "total": 10,
  "page": 1,
  "page_size": 20,
  "pages": 1,
  "data": [
    {
      "id": "uuid",
      "execution_id": "uuid",
      "node_id": "approval_1",
      "node_name": "经理审批",
      "status": "pending",
      "assignee_type": "user",
      "assignee_id": "uuid",
      "created_at": "2024-01-01T00:00:00"
    }
  ]
}
```

#### 获取审批详情
```
GET /api/v1/approvals/{approval_id}
Authorization: Bearer {token}
```

#### 审批通过
```
POST /api/v1/approvals/{approval_id}/approve
Authorization: Bearer {token}
Content-Type: application/json

{
  "comment": "同意申请"
}
```

#### 审批拒绝
```
POST /api/v1/approvals/{approval_id}/reject
Authorization: Bearer {token}
Content-Type: application/json

{
  "comment": "信息不完整，请补充"
}
```

#### 转办
```
POST /api/v1/approvals/{approval_id}/transfer
Authorization: Bearer {token}
Content-Type: application/json

{
  "new_assignee_id": "uuid",
  "comment": "请协助审批"
}
```

#### 获取已审批列表
```
GET /api/v1/approvals/my?page=1&page_size=20&status=approved
Authorization: Bearer {token}
```

### 4. 审批节点配置

在工作流定义中添加审批节点:

```json
{
  "id": "approval_1",
  "type": "approval",
  "position": {"x": 300, "y": 200},
  "data": {
    "label": "经理审批",
    "assignee_type": "user",
    "assignee_id": "user_uuid",
    "timeout": 86400,
    "auto_action": "reject"
  }
}
```

#### 配置说明

| 配置项 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| label | str | 是 | - | 节点显示名称 |
| assignee_type | str | 是 | user | 指派类型: user/role/department |
| assignee_id | UUID | 是 | - | 指派人/角色/部门ID |
| timeout | int | 否 | 86400 | 超时时间(秒) |
| auto_action | str | 否 | reject | 超时自动操作: approve/reject |

#### 指派类型说明

- **user**: 指定特定用户审批
- **role**: 指定角色，该角色下任意成员均可审批
- **department**: 指定部门，该部门下任意成员均可审批

### 5. 服务层 (backend/app/services/workflow_service.py)

**ApprovalTaskService 方法:**

- `create_task()` - 创建审批任务
- `get_task_by_id()` - 根据ID获取任务
- `list_pending_tasks()` - 获取待审批列表
- `list_user_tasks()` - 获取用户已审批列表
- `approve_task()` - 审批通过
- `reject_task()` - 审批拒绝
- `transfer_task()` - 转办任务
- `check_user_can_approve()` - 检查用户是否有权限审批

## 使用示例

### 创建工作流

1. 在设计器中创建包含审批节点的工作流
2. 配置审批节点的指派信息
3. 发布工作流

### 执行工作流

```bash
# 启动工作流执行
POST /api/v1/workflows/{workflow_id}/execute
{
  "input_data": {"request_type": "leave", "days": 5},
  "synchronous": true
}
```

### 处理审批

1. 用户登录后调用 `GET /api/v1/approvals/pending` 获取待审批列表
2. 查看审批详情和输入数据
3. 执行审批操作（通过/拒绝/转办）

## 注意事项

1. **权限检查**: 审批操作前会检查用户是否有权限（基于assignee_type和assignee_id）
2. **状态检查**: 只有pending状态的任务才能进行审批操作
3. **超时处理**: 需要配合定时任务实现超时自动处理
4. **工作流恢复**: 审批完成后需要调用工作流引擎接口继续执行工作流

## 后续扩展

1. **会签功能**: 支持多人同时审批，全部通过才算通过
2. **或签功能**: 支持多人中任意一人审批即可
3. **审批历史**: 记录完整的审批过程
4. **审批委托**: 支持设置代理人处理审批
5. **超时提醒**: 审批即将超时发送提醒通知
