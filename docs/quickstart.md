# 快速开始

## 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- Node.js 20+ (本地开发)
- Python 3.11+ (本地开发)

## 使用 Docker Compose 启动

### 1. 克隆项目

```bash
cd enterprise-workflow-platform
```

### 2. 启动服务

```bash
docker-compose up -d
```

### 3. 访问应用

- 前端界面: http://localhost:8080
- API文档: http://localhost:8080/api/docs

### 4. 默认账号

- 用户名: `admin`
- 密码: `admin123`

## 本地开发

### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
cp .env.example .env
# 编辑 .env 文件配置数据库连接

# 启动开发服务器
uvicorn app.main:app --reload
```

后端服务将在 http://localhost:8000 运行

### 前端开发

```bash
cd frontend

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

前端服务将在 http://localhost:5173 运行

## 项目结构

```
enterprise-workflow-platform/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心配置
│   │   ├── db/             # 数据库
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # 业务逻辑
│   │   ├── workflow/       # 工作流引擎
│   │   └── main.py         # 应用入口
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React 前端
│   ├── src/
│   │   ├── components/     # 组件
│   │   ├── pages/          # 页面
│   │   ├── services/       # API服务
│   │   ├── stores/         # 状态管理
│   │   └── main.tsx        # 应用入口
│   ├── package.json
│   └── Dockerfile
├── docker/                 # Docker配置
├── docs/                   # 文档
└── docker-compose.yml
```

## 创建第一个工作流

### 1. 登录系统

访问 http://localhost:8080 并使用默认账号登录。

### 2. 创建组件

1. 进入"组件管理"页面
2. 点击"创建组件"
3. 选择组件类型 (API/数据库/AI等)
4. 配置输入输出参数
5. 保存并发布

### 3. 设计工作流

1. 进入"工作流管理"页面
2. 点击"创建工作流"
3. 从左侧组件库拖拽节点到画布
4. 连接节点定义执行顺序
5. 配置每个节点的参数
6. 保存并发布

### 4. 执行工作流

1. 在工作流详情页点击"执行"
2. 输入必要的参数
3. 查看执行结果和日志

## 集成MCP

### 1. 添加MCP服务器

```bash
curl -X POST http://localhost:8000/api/v1/mcp/servers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{
    "name": "文件系统",
    "code": "filesystem",
    "transport_type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
  }'
```

### 2. 在工作流中使用MCP

1. 在工作流设计器中添加 MCP 节点
2. 选择已注册的MCP服务器
3. 选择要调用的工具
4. 配置参数映射

## 创建Agent技能

### 1. 定义技能

```json
{
  "name": "数据查询助手",
  "code": "data_query",
  "description": "帮助用户查询和分析数据",
  "definition": {
    "system_prompt": "你是一个数据分析助手...",
    "tools": ["query_database", "generate_report"],
    "model_config": {
      "model": "gpt-4",
      "temperature": 0.7
    }
  }
}
```

### 2. 在工作流中使用Agent

1. 在工作流设计器中添加 Agent 节点
2. 选择定义好的技能
3. 配置输入输出映射

## 常见问题

### Q: 数据库连接失败？

A: 检查 `DATABASE_URL` 环境变量是否正确配置。

### Q: 前端API请求失败？

A: 检查 `vite.config.ts` 中的 proxy 配置是否正确。

### Q: 如何添加自定义组件？

A: 参考 `backend/app/workflow/engine.py` 中的组件定义，实现自定义处理器。

## 下一步

- 阅读 [架构设计](architecture.md) 了解系统架构
- 阅读 [API文档](api.md) 了解API详情
- 阅读 [开发指南](development.md) 了解开发规范
