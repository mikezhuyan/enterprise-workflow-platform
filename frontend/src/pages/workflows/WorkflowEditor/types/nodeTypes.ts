/**
 * 工作流节点类型定义
 */

export type NodeCategory = 'control' | 'api' | 'database' | 'message' | 'ai' | 'mcp';

export interface NodeTypeDefinition {
  type: string;
  name: string;
  category: NodeCategory;
  icon: string;
  color: string;
  shape: 'circle' | 'rect' | 'diamond' | 'rounded-rect';
  description?: string;
  // 端口配置
  ports: {
    inputs: number;  // 输入端口数量
    outputs: number | 'dynamic';  // 输出端口数量，'dynamic'表示动态（如条件分支）
  };
  // 配置表单字段
  configFields: ConfigField[];
  // 是否需要选择具体组件
  requiresComponent: boolean;
  // 组件筛选条件
  componentFilter?: {
    component_type?: string;
    protocol?: string;
  };
}

export interface ConfigField {
  name: string;
  label: string;
  type: 'string' | 'number' | 'boolean' | 'json' | 'textarea' | 'select' | 'code' | 'component-select';
  required?: boolean;
  defaultValue?: any;
  options?: { label: string; value: string }[];
  description?: string;
  placeholder?: string;
}

// 节点类型定义
export const nodeTypeDefinitions: Record<string, NodeTypeDefinition> = {
  // 控制节点
  start: {
    type: 'start',
    name: '开始',
    category: 'control',
    icon: 'PlayCircleFilled',
    color: '#52c41a',
    shape: 'circle',
    description: '工作流起点',
    ports: { inputs: 0, outputs: 1 },
    configFields: [],
    requiresComponent: false,
  },
  end: {
    type: 'end',
    name: '结束',
    category: 'control',
    icon: 'PauseCircleFilled',
    color: '#ff4d4f',
    shape: 'circle',
    description: '工作流终点',
    ports: { inputs: 1, outputs: 0 },
    configFields: [
      {
        name: 'output',
        label: '输出变量',
        type: 'json',
        description: '定义工作流输出',
      },
    ],
    requiresComponent: false,
  },
  condition: {
    type: 'condition',
    name: '条件判断',
    category: 'control',
    icon: 'BranchesOutlined',
    color: '#fa8c16',
    shape: 'diamond',
    description: '根据条件分支执行不同路径',
    ports: { inputs: 1, outputs: 'dynamic' },
    configFields: [
      {
        name: 'conditions',
        label: '分支条件',
        type: 'json',
        required: true,
        description: '定义条件分支，格式: [{"name": "分支1", "condition": "{{variable}} > 0"}]',
      },
      {
        name: 'defaultBranch',
        label: '默认分支名称',
        type: 'string',
        defaultValue: '默认',
        description: '当所有条件不满足时的分支名称',
      },
    ],
    requiresComponent: false,
  },
  delay: {
    type: 'delay',
    name: '延时',
    category: 'control',
    icon: 'ClockCircleOutlined',
    color: '#eb2f96',
    shape: 'rounded-rect',
    description: '延迟执行',
    ports: { inputs: 1, outputs: 1 },
    configFields: [
      {
        name: 'delay',
        label: '延迟时间(秒)',
        type: 'number',
        required: true,
        defaultValue: 5,
        description: '延迟执行的秒数',
      },
    ],
    requiresComponent: false,
  },

  // API组件 - 支持多种微服务协议
  api: {
    type: 'api',
    name: 'API调用',
    category: 'api',
    icon: 'ApiOutlined',
    color: '#1890ff',
    shape: 'rounded-rect',
    description: '调用HTTP/gRPC/GraphQL/SOAP/WebSocket等API服务',
    ports: { inputs: 1, outputs: 1 },
    configFields: [
      {
        name: 'protocol',
        label: '协议类型',
        type: 'select',
        required: true,
        defaultValue: 'http',
        options: [
          { label: 'HTTP/HTTPS', value: 'http' },
          { label: 'gRPC', value: 'grpc' },
          { label: 'GraphQL', value: 'graphql' },
          { label: 'SOAP', value: 'soap' },
          { label: 'WebSocket', value: 'websocket' },
        ],
      },
      {
        name: 'componentId',
        label: '选择已注册组件',
        type: 'component-select',
        description: '从已注册的API组件中选择并复用其配置',
      },
      // HTTP协议配置
      {
        name: 'method',
        label: '请求方法',
        type: 'select',
        required: true,
        defaultValue: 'GET',
        options: [
          { label: 'GET', value: 'GET' },
          { label: 'POST', value: 'POST' },
          { label: 'PUT', value: 'PUT' },
          { label: 'DELETE', value: 'DELETE' },
          { label: 'PATCH', value: 'PATCH' },
        ],
      },
      {
        name: 'url',
        label: '请求URL',
        type: 'string',
        required: true,
        placeholder: 'https://api.example.com/data',
      },
      {
        name: 'headers',
        label: '请求头',
        type: 'json',
        description: 'JSON格式的请求头',
      },
      {
        name: 'body',
        label: '请求体',
        type: 'json',
        description: 'JSON格式的请求体（仅POST/PUT/PATCH）',
      },
      // gRPC协议配置
      {
        name: 'target',
        label: 'gRPC服务地址',
        type: 'string',
        placeholder: 'localhost:50051',
      },
      {
        name: 'service',
        label: '服务名',
        type: 'string',
        placeholder: 'UserService',
      },
      {
        name: 'method',
        label: '方法名',
        type: 'string',
        placeholder: 'GetUser',
      },
      {
        name: 'protoFile',
        label: 'Proto文件内容',
        type: 'textarea',
        description: 'Protocol Buffer定义文件',
      },
      // GraphQL协议配置
      {
        name: 'endpoint',
        label: 'GraphQL端点',
        type: 'string',
        placeholder: 'https://api.example.com/graphql',
      },
      {
        name: 'query',
        label: '查询语句',
        type: 'textarea',
        description: 'GraphQL查询或变更语句',
      },
      {
        name: 'variables',
        label: '变量',
        type: 'json',
        description: 'GraphQL变量（JSON格式）',
      },
      // SOAP协议配置
      {
        name: 'soapUrl',
        label: 'SOAP地址',
        type: 'string',
        placeholder: 'http://example.com/soap',
      },
      {
        name: 'soapAction',
        label: 'SOAP Action',
        type: 'string',
      },
      {
        name: 'soapBody',
        label: 'SOAP Body (XML)',
        type: 'textarea',
      },
      // WebSocket协议配置
      {
        name: 'wsUrl',
        label: 'WebSocket地址',
        type: 'string',
        placeholder: 'wss://ws.example.com/socket',
      },
      {
        name: 'wsMessage',
        label: '发送消息',
        type: 'json',
        description: '要发送的WebSocket消息',
      },
      // 通用配置
      {
        name: 'timeout',
        label: '超时时间(秒)',
        type: 'number',
        defaultValue: 30,
      },
    ],
    requiresComponent: false,
  },

  // 数据库组件
  database: {
    type: 'database',
    name: '数据库操作',
    category: 'database',
    icon: 'DatabaseOutlined',
    color: '#52c41a',
    shape: 'rounded-rect',
    description: '执行数据库查询或操作',
    ports: { inputs: 1, outputs: 1 },
    configFields: [
      {
        name: 'dbType',
        label: '数据库类型',
        type: 'select',
        required: true,
        options: [
          { label: 'PostgreSQL', value: 'postgresql' },
          { label: 'MySQL', value: 'mysql' },
          { label: 'MongoDB', value: 'mongodb' },
          { label: 'Redis', value: 'redis' },
        ],
      },
      {
        name: 'connection',
        label: '连接字符串',
        type: 'string',
        required: true,
        placeholder: 'postgresql://user:pass@host:port/db',
      },
      {
        name: 'operation',
        label: '操作类型',
        type: 'select',
        required: true,
        options: [
          { label: '查询', value: 'query' },
          { label: '插入', value: 'insert' },
          { label: '更新', value: 'update' },
          { label: '删除', value: 'delete' },
        ],
      },
      {
        name: 'sql',
        label: 'SQL/查询语句',
        type: 'textarea',
        required: true,
        placeholder: 'SELECT * FROM users WHERE id = {{userId}}',
      },
    ],
    requiresComponent: true,
    componentFilter: { component_type: 'database' },
  },

  // AI组件
  llm: {
    type: 'llm',
    name: 'AI/LLM',
    category: 'ai',
    icon: 'RobotOutlined',
    color: '#722ed1',
    shape: 'rounded-rect',
    description: '调用大语言模型',
    ports: { inputs: 1, outputs: 1 },
    configFields: [
      {
        name: 'model',
        label: '模型',
        type: 'select',
        required: true,
        options: [
          { label: 'GPT-4', value: 'gpt-4' },
          { label: 'GPT-3.5', value: 'gpt-3.5-turbo' },
          { label: 'Claude', value: 'claude' },
          { label: '本地模型', value: 'local' },
        ],
      },
      {
        name: 'prompt',
        label: '提示词',
        type: 'textarea',
        required: true,
        placeholder: '请输入提示词，可使用 {{variable}} 引用变量',
      },
      {
        name: 'temperature',
        label: 'Temperature',
        type: 'number',
        defaultValue: 0.7,
        description: '控制输出的随机性，范围0-1',
      },
      {
        name: 'maxTokens',
        label: '最大Token数',
        type: 'number',
        defaultValue: 2000,
      },
      {
        name: 'systemPrompt',
        label: '系统提示词',
        type: 'textarea',
        description: '定义AI的角色和行为',
      },
      {
        name: 'outputFormat',
        label: '输出格式',
        type: 'select',
        defaultValue: 'text',
        options: [
          { label: '文本', value: 'text' },
          { label: 'JSON', value: 'json' },
        ],
      },
    ],
    requiresComponent: true,
    componentFilter: { component_type: 'ai', protocol: 'llm' },
  },

  // MCP组件
  mcp: {
    type: 'mcp',
    name: 'MCP工具',
    category: 'mcp',
    icon: 'CloudOutlined',
    color: '#13c2c2',
    shape: 'rounded-rect',
    description: '调用MCP(Model Context Protocol)工具',
    ports: { inputs: 1, outputs: 1 },
    configFields: [
      {
        name: 'serverUrl',
        label: 'MCP服务器地址',
        type: 'string',
        required: true,
        placeholder: 'http://localhost:3000/sse',
      },
      {
        name: 'toolName',
        label: '工具名称',
        type: 'string',
        required: true,
        description: '要调用的MCP工具名',
      },
      {
        name: 'parameters',
        label: '参数',
        type: 'json',
        description: '工具参数，JSON格式',
      },
      {
        name: 'timeout',
        label: '超时时间(秒)',
        type: 'number',
        defaultValue: 60,
      },
    ],
    requiresComponent: true,
    componentFilter: { component_type: 'ai', protocol: 'mcp' },
  },

  // 脚本组件
  script: {
    type: 'script',
    name: '脚本',
    category: 'api',
    icon: 'CodeOutlined',
    color: '#faad14',
    shape: 'rounded-rect',
    description: '执行自定义脚本',
    ports: { inputs: 1, outputs: 1 },
    configFields: [
      {
        name: 'language',
        label: '脚本语言',
        type: 'select',
        required: true,
        options: [
          { label: 'Python', value: 'python' },
          { label: 'JavaScript', value: 'javascript' },
          { label: 'Bash', value: 'bash' },
        ],
      },
      {
        name: 'code',
        label: '脚本代码',
        type: 'code',
        required: true,
        description: '编写脚本代码，可使用 input 变量访问输入',
      },
    ],
    requiresComponent: false,
  },

  // 函数组件
  function: {
    type: 'function',
    name: '函数',
    category: 'api',
    icon: 'FunctionOutlined',
    color: '#722ed1',
    shape: 'rounded-rect',
    description: '调用自定义函数',
    ports: { inputs: 1, outputs: 1 },
    configFields: [
      {
        name: 'functionName',
        label: '函数名称',
        type: 'string',
        required: true,
      },
      {
        name: 'parameters',
        label: '参数',
        type: 'json',
        description: '函数参数',
      },
    ],
    requiresComponent: false,
  },

  // 消息组件
  email: {
    type: 'email',
    name: '发送邮件',
    category: 'message',
    icon: 'MailOutlined',
    color: '#1890ff',
    shape: 'rounded-rect',
    description: '发送电子邮件',
    ports: { inputs: 1, outputs: 1 },
    configFields: [
      {
        name: 'to',
        label: '收件人',
        type: 'string',
        required: true,
        placeholder: 'user@example.com',
      },
      {
        name: 'subject',
        label: '主题',
        type: 'string',
        required: true,
      },
      {
        name: 'body',
        label: '邮件内容',
        type: 'textarea',
        required: true,
      },
      {
        name: 'html',
        label: 'HTML格式',
        type: 'boolean',
        defaultValue: false,
      },
    ],
    requiresComponent: false,
  },
};

// 获取节点类型定义
export const getNodeTypeDefinition = (type: string): NodeTypeDefinition | undefined => {
  return nodeTypeDefinitions[type];
};

// 获取所有节点类型列表
export const getAllNodeTypes = (): NodeTypeDefinition[] => {
  return Object.values(nodeTypeDefinitions);
};

// 按分类获取节点类型
export const getNodeTypesByCategory = (category: NodeCategory): NodeTypeDefinition[] => {
  return Object.values(nodeTypeDefinitions).filter(n => n.category === category);
};
