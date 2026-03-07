# API 文档

## 认证

### 登录
```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

响应:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid",
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "管理员",
    "is_superuser": true,
    "roles": []
  }
}
```

### 刷新Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGc..."
}
```

### 获取当前用户
```http
GET /api/v1/auth/me
Authorization: Bearer {token}
```

## 用户管理

### 用户列表
```http
GET /api/v1/users?page=1&page_size=20&search=keyword
```

### 创建用户
```http
POST /api/v1/users
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "password123",
  "full_name": "新用户",
  "role_ids": []
}
```

### 更新用户
```http
PUT /api/v1/users/{user_id}
Content-Type: application/json

{
  "email": "newemail@example.com",
  "full_name": "更新名称"
}
```

### 删除用户
```http
DELETE /api/v1/users/{user_id}
```

## 工作流管理

### 工作流列表
```http
GET /api/v1/workflows?page=1&page_size=20&category_id=xxx
```

### 创建工作流
```http
POST /api/v1/workflows
Content-Type: application/json

{
  "name": "订单处理流程",
  "description": "处理新订单的自动化流程",
  "definition": {
    "nodes": [
      {"id": "start", "type": "start", "position": {"x": 100, "y": 100}},
      {"id": "api1", "type": "api", "position": {"x": 300, "y": 100}, "data": {...}}
    ],
    "edges": [
      {"id": "e1", "source": "start", "target": "api1"}
    ]
  },
  "variables": [
    {"name": "orderId", "type": "string", "required": true}
  ]
}
```

### 更新工作流
```http
PUT /api/v1/workflows/{workflow_id}
Content-Type: application/json
```

### 删除工作流
```http
DELETE /api/v1/workflows/{workflow_id}
```

### 发布工作流
```http
POST /api/v1/workflows/{workflow_id}/publish
```

### 执行工作流
```http
POST /api/v1/workflows/{workflow_id}/execute
Content-Type: application/json

{
  "input_data": {
    "orderId": "ORD123456"
  },
  "synchronous": true,
  "timeout": 300
}
```

### 获取执行记录
```http
GET /api/v1/workflows/{workflow_id}/executions
```

### 获取执行详情
```http
GET /api/v1/workflows/executions/{execution_id}
```

## 组件管理

### 组件列表
```http
GET /api/v1/components?page=1&page_size=20&type=api
```

### 创建组件
```http
POST /api/v1/components
Content-Type: application/json

{
  "name": "发送邮件",
  "code": "send_email",
  "description": "发送邮件通知",
  "component_type": "api",
  "input_schema": {
    "type": "object",
    "properties": {
      "to": {"type": "string"},
      "subject": {"type": "string"},
      "body": {"type": "string"}
    },
    "required": ["to", "subject", "body"]
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "messageId": {"type": "string"},
      "status": {"type": "string"}
    }
  },
  "execution_config": {
    "url": "https://api.example.com/send-email",
    "method": "POST"
  }
}
```

### 测试组件
```http
POST /api/v1/components/{component_id}/test
Content-Type: application/json

{
  "input_data": {
    "to": "test@example.com",
    "subject": "测试邮件",
    "body": "这是一封测试邮件"
  },
  "config": {}
}
```

## MCP 管理

### MCP服务器列表
```http
GET /api/v1/mcp/servers
```

### 创建MCP服务器
```http
POST /api/v1/mcp/servers
Content-Type: application/json

{
  "name": "文件系统MCP",
  "code": "filesystem_mcp",
  "transport_type": "stdio",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/files"]
}
```

### 列出MCP工具
```http
GET /api/v1/mcp/servers/{server_id}/tools
```

## Agent 管理

### Agent技能列表
```http
GET /api/v1/agents/skills
```

### 创建Agent技能
```http
POST /api/v1/agents/skills
Content-Type: application/json

{
  "name": "数据分析助手",
  "code": "data_analyst",
  "description": "帮助用户分析数据并生成报告",
  "definition": {
    "system_prompt": "你是一个数据分析专家...",
    "tools": ["query_database", "generate_chart"],
    "model_config": {
      "model": "gpt-4",
      "temperature": 0.7
    }
  }
}
```

## 错误响应

### 400 Bad Request
```json
{
  "detail": "请求参数错误"
}
```

### 401 Unauthorized
```json
{
  "detail": "未授权"
}
```

### 403 Forbidden
```json
{
  "detail": "权限不足"
}
```

### 404 Not Found
```json
{
  "detail": "资源不存在"
}
```

### 500 Internal Server Error
```json
{
  "detail": "服务器内部错误"
}
```
