import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Button,
  Space,
  Input,
  Form,
  Select,
  Tabs,
  message,
  Radio,
  Divider,
  Alert,
  Tag,
  Row,
  Col,
  InputNumber,
  Switch,
  Collapse,
  Table,
  Modal,
} from 'antd'
import {
  SaveOutlined,
  RollbackOutlined,
  PlayCircleOutlined,
  PlusOutlined,
  DeleteOutlined,
  ApiOutlined,
  DatabaseOutlined,
  RobotOutlined,
  CloudOutlined,
  CodeOutlined,
  BranchesOutlined,
  ClockCircleOutlined,
  MailOutlined,
  FileTextOutlined,
  FunctionOutlined,
  NodeIndexOutlined,
  GlobalOutlined,
} from '@ant-design/icons'
import { post, get, put } from '../../../services/request'
import { ProtocolConfigForm } from './ProtocolConfigForm'
import { SchemaEditor } from './SchemaEditor'

const { TabPane } = Tabs
const { TextArea } = Input
const { Option } = Select
const { Panel } = Collapse

// 组件类型定义
const componentTypes = [
  { value: 'api', label: 'API服务', icon: <ApiOutlined />, color: 'blue', protocols: ['http', 'https', 'grpc', 'graphql', 'soap', 'websocket'] },
  { value: 'database', label: '数据库', icon: <DatabaseOutlined />, color: 'green', protocols: ['postgresql', 'mysql', 'mongodb', 'redis'] },
  { value: 'message', label: '消息队列', icon: <NodeIndexOutlined />, color: 'orange', protocols: ['kafka', 'rabbitmq', 'mqtt'] },
  { value: 'script', label: '脚本执行', icon: <CodeOutlined />, color: 'purple', protocols: ['python', 'javascript', 'shell'] },
  { value: 'ai', label: 'AI/LLM', icon: <RobotOutlined />, color: 'magenta', protocols: ['openai', 'anthropic', 'custom'] },
  { value: 'function', label: '自定义函数', icon: <FunctionOutlined />, color: 'cyan', protocols: ['javascript', 'python'] },
]

// 协议配置模板
const protocolTemplates: Record<string, any> = {
  http: {
    protocol: 'http',
    method: 'GET',
    url: 'http://example.com/api',
    headers: { 'Content-Type': 'application/json' },
    params: {},
    body: '{}',
    timeout: 30,
    verify_ssl: true,
  },
  https: {
    protocol: 'https',
    method: 'POST',
    url: 'https://api.example.com/v1/resource',
    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer {{token}}' },
    params: {},
    body: '{\n  "key": "value"\n}',
    timeout: 30,
    verify_ssl: true,
  },
  graphql: {
    protocol: 'graphql',
    url: 'https://api.example.com/graphql',
    query: 'query GetUser($id: ID!) {\n  user(id: $id) {\n    id\n    name\n    email\n  }\n}',
    variables: { id: '{{userId}}' },
    headers: { 'Content-Type': 'application/json' },
  },
  grpc: {
    protocol: 'grpc',
    target: 'localhost:50051',
    service: 'UserService',
    method: 'GetUser',
    proto_file: '',
    metadata: {},
  },
  soap: {
    protocol: 'soap',
    url: 'http://example.com/soap',
    soap_action: 'http://example.com/GetUser',
    body: '<?xml version="1.0"?>\n<soap:Envelope>\n  <soap:Body>\n    <GetUser>\n      <id>{{userId}}</id>\n    </GetUser>\n  </soap:Body>\n</soap:Envelope>',
    headers: {},
  },
  postgresql: {
    protocol: 'postgresql',
    connection_string: 'postgresql://user:pass@localhost:5432/dbname',
    sql: 'SELECT * FROM users WHERE id = {{userId}}',
    timeout: 30,
  },
  mysql: {
    protocol: 'mysql',
    connection_string: 'mysql://user:pass@localhost:3306/dbname',
    sql: 'SELECT * FROM users WHERE id = {{userId}}',
    timeout: 30,
  },
  mongodb: {
    protocol: 'mongodb',
    connection_string: 'mongodb://localhost:27017/dbname',
    collection: 'users',
    operation: 'find',
    filter: '{ "id": "{{userId}}" }',
  },
  kafka: {
    protocol: 'kafka',
    brokers: 'localhost:9092',
    topic: 'my-topic',
    message: '{\n  "key": "value"\n}',
    key: '{{userId}}',
  },
  rabbitmq: {
    protocol: 'rabbitmq',
    host: 'localhost',
    port: 5672,
    queue: 'my-queue',
    exchange: '',
    routing_key: 'my-key',
    message: '{\n  "data": "value"\n}',
  },
  python: {
    protocol: 'python',
    code: '# Python脚本\ndef main(input_data):\n    # 处理输入数据\n    result = {\n        "message": "Hello from Python",\n        "input": input_data\n    }\n    return result\n\n# 执行函数\noutput = main(input_data)',
  },
  javascript: {
    protocol: 'javascript',
    code: '// JavaScript脚本\nasync function main(inputData) {\n    // 处理输入数据\n    const result = {\n        message: "Hello from JavaScript",\n        input: inputData,\n        timestamp: new Date().toISOString()\n    };\n    return result;\n}\n\n// 执行函数\nmain(input_data).then(output => {\n    // 返回结果\n});',
  },
  openai: {
    protocol: 'openai',
    model: 'gpt-4',
    api_key: '{{OPENAI_API_KEY}}',
    system_prompt: '你是一个有用的助手。',
    user_prompt: '{{input}}',
    temperature: 0.7,
    max_tokens: 1000,
  },
}

export const ComponentEditorPage = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEditing = !!id
  const [form] = Form.useForm()
  const [activeTab, setActiveTab] = useState('basic')
  const [componentType, setComponentType] = useState('api')
  const [protocol, setProtocol] = useState('http')
  const [executionConfig, setExecutionConfig] = useState<any>({})
  const [inputSchema, setInputSchema] = useState<any>({ type: 'object', properties: {}, required: [] })
  const [outputSchema, setOutputSchema] = useState<any>({ type: 'object', properties: {}, required: [] })
  const [testModalVisible, setTestModalVisible] = useState(false)
  const [testInput, setTestInput] = useState('{}')
  const [testResult, setTestResult] = useState<any>(null)
  const [testLoading, setTestLoading] = useState(false)
  const [loading, setLoading] = useState(false)
  const [componentData, setComponentData] = useState<any>(null)

  useEffect(() => {
    if (isEditing && id) {
      fetchComponent(id)
    } else {
      // 新建组件，设置默认值
      setExecutionConfig(protocolTemplates['http'])
    }
  }, [id, isEditing])

  const fetchComponent = async (componentId: string) => {
    try {
      setLoading(true)
      const data: any = await get(`/components/${componentId}`)
      setComponentData(data)
      
      // 填充表单
      form.setFieldsValue({
        name: data.name,
        code: data.code,
        description: data.description,
        component_type: data.component_type,
      })
      
      setComponentType(data.component_type)
      setInputSchema(data.input_schema || { type: 'object', properties: {}, required: [] })
      setOutputSchema(data.output_schema || { type: 'object', properties: {}, required: [] })
      setExecutionConfig(data.execution_config || {})
      if (data.execution_config?.protocol) {
        setProtocol(data.execution_config.protocol)
      }
    } catch (error) {
      message.error('获取组件信息失败')
    } finally {
      setLoading(false)
    }
  }

  const handleTypeChange = (type: string) => {
    setComponentType(type)
    const typeInfo = componentTypes.find(t => t.value === type)
    if (typeInfo && typeInfo.protocols.length > 0) {
      const newProtocol = typeInfo.protocols[0]
      setProtocol(newProtocol)
      setExecutionConfig(protocolTemplates[newProtocol] || {})
    }
  }

  const handleProtocolChange = (proto: string) => {
    setProtocol(proto)
    setExecutionConfig(protocolTemplates[proto] || { protocol: proto })
  }

  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      
      const payload = {
        ...values,
        input_schema: inputSchema,
        output_schema: outputSchema,
        execution_config: executionConfig,
      }
      
      if (isEditing) {
        await put(`/components/${id}`, payload)
        message.success('组件更新成功')
      } else {
        await post('/components', payload)
        message.success('组件创建成功')
        navigate('/components')
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '保存失败')
    }
  }

  const handleTest = async () => {
    if (!isEditing) {
      message.warning('请先保存组件后再测试')
      return
    }
    setTestModalVisible(true)
  }

  const runTest = async () => {
    try {
      setTestLoading(true)
      const inputData = JSON.parse(testInput)
      const result = await post(`/components/${id}/test`, { input_data: inputData })
      setTestResult(result)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '测试失败')
    } finally {
      setTestLoading(false)
    }
  }

  const handleBack = () => {
    navigate('/components')
  }



  const typeInfo = componentTypes.find(t => t.value === componentType)

  return (
    <div className="component-editor-page">
      <Card
        title={isEditing ? '编辑组件' : '注册组件'}
        extra={
          <Space>
            <Button icon={<RollbackOutlined />} onClick={handleBack}>
              返回
            </Button>
            <Button icon={<PlayCircleOutlined />} onClick={handleTest} disabled={!isEditing}>
              测试
            </Button>
            <Button type="primary" icon={<SaveOutlined />} onClick={handleSave} loading={loading}>
              保存
            </Button>
          </Space>
        }
      >
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="基本信息" key="basic">
            <Form form={form} layout="vertical" style={{ maxWidth: 800 }}>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="name"
                    label="组件名称"
                    rules={[{ required: true, message: '请输入组件名称' }]}
                  >
                    <Input placeholder="输入组件名称" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="code"
                    label="组件编码"
                    rules={[{ required: true, message: '请输入组件编码' }]}
                  >
                    <Input placeholder="唯一标识，如: send_email" disabled={isEditing} />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item name="description" label="组件描述">
                <TextArea rows={3} placeholder="描述组件的功能和用途" />
              </Form.Item>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="component_type"
                    label="组件类型"
                    rules={[{ required: true }]}
                  >
                    <Select placeholder="选择组件类型" onChange={handleTypeChange}>
                      {componentTypes.map(type => (
                        <Option key={type.value} value={type.value}>
                          <Space>
                            <span style={{ color: type.color }}>{type.icon}</span>
                            {type.label}
                          </Space>
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="协议类型">
                    <Select value={protocol} onChange={handleProtocolChange}>
                      {typeInfo?.protocols.map(p => (
                        <Option key={p} value={p}>{p.toUpperCase()}</Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Alert
                message={`当前配置: ${typeInfo?.label || 'API服务'} - ${protocol.toUpperCase()} 协议`}
                description={`支持 ${typeInfo?.protocols.join(', ')} 等协议`}
                type="info"
                showIcon
                style={{ marginBottom: 24 }}
              />
            </Form>
          </TabPane>

          <TabPane tab="协议配置" key="protocol">
            <div style={{ maxWidth: 800 }}>
              <h4 style={{ marginBottom: 16 }}>
                <Tag color="blue">{protocol.toUpperCase()}</Tag>
                协议配置
              </h4>
              <ProtocolConfigForm
                protocol={protocol}
                executionConfig={executionConfig}
                onChange={setExecutionConfig}
              />
            </div>
          </TabPane>

          <TabPane tab="输入参数" key="input">
            <div style={{ maxWidth: 800 }}>
              <SchemaEditor
                title="输入参数定义"
                value={inputSchema}
                onChange={setInputSchema}
              />
            </div>
          </TabPane>

          <TabPane tab="输出定义" key="output">
            <div style={{ maxWidth: 800 }}>
              <SchemaEditor
                title="输出参数定义"
                value={outputSchema}
                onChange={setOutputSchema}
              />
            </div>
          </TabPane>

          <TabPane tab="使用文档" key="docs">
            <Form layout="vertical" style={{ maxWidth: 800 }}>
              <Form.Item label="使用说明">
                <TextArea
                  rows={15}
                  placeholder="# 使用说明&#10;&#10;## 参数说明&#10;...&#10;&#10;## 示例&#10;..."
                />
              </Form.Item>
            </Form>
          </TabPane>
        </Tabs>
      </Card>

      {/* 测试弹窗 */}
      <Modal
        title="测试组件"
        open={testModalVisible}
        onCancel={() => setTestModalVisible(false)}
        footer={null}
        width={800}
      >
        <div style={{ marginBottom: 16 }}>
          <h4>测试输入数据 (JSON)</h4>
          <TextArea
            rows={6}
            value={testInput}
            onChange={e => setTestInput(e.target.value)}
            placeholder='{"key": "value"}'
            style={{ marginBottom: 8 }}
          />
          <Button type="primary" icon={<PlayCircleOutlined />} onClick={runTest} loading={testLoading}>
            运行测试
          </Button>
        </div>

        {testResult && (
          <div>
            <Divider />
            <h4>测试结果</h4>
            <Alert
              message={testResult.success ? '执行成功' : '执行失败'}
              type={testResult.success ? 'success' : 'error'}
              showIcon
              style={{ marginBottom: 16 }}
            />
            <div style={{ background: '#f5f5f5', padding: 16, borderRadius: 4 }}>
              <div style={{ marginBottom: 8, color: '#666' }}>
                执行时间: {testResult.duration_ms}ms
              </div>
              <pre style={{ margin: 0, overflow: 'auto' }}>
                {JSON.stringify(testResult.output_data || testResult, null, 2)}
              </pre>
            </div>
            {testResult.logs && testResult.logs.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <h5>执行日志:</h5>
                <div style={{ background: '#1e1e1e', color: '#d4d4d4', padding: 12, borderRadius: 4, fontSize: 12, fontFamily: 'monospace' }}>
                  {testResult.logs.map((log: string, i: number) => (
                    <div key={i}>{log}</div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default ComponentEditorPage
