import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Card,
  Button,
  Table,
  Input,
  Tag,
  Dropdown,
  message,
  Popconfirm,
  Space,
  Select,
  Tabs,
  Badge,
  Tooltip,
  Modal,
  Form,
  Row,
  Col,
  Divider,
  Spin,
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  MoreOutlined,
  PlayCircleOutlined,
  EditOutlined,
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
  ThunderboltOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseOutlined,
} from '@ant-design/icons'
import { get, del, post } from '../../../services/request'

const { Search } = Input
const { Option } = Select
const { TabPane } = Tabs
const { TextArea } = Input

const componentTypeMap: Record<string, { icon: any, color: string, label: string }> = {
  api: { icon: <ApiOutlined />, color: 'blue', label: 'API服务' },
  database: { icon: <DatabaseOutlined />, color: 'green', label: '数据库' },
  message: { icon: <NodeIndexOutlined />, color: 'orange', label: '消息队列' },
  script: { icon: <CodeOutlined />, color: 'purple', label: '脚本' },
  ai: { icon: <RobotOutlined />, color: 'magenta', label: 'AI/LLM' },
  function: { icon: <FunctionOutlined />, color: 'cyan', label: '自定义函数' },
  condition: { icon: <BranchesOutlined />, color: 'gold', label: '条件判断' },
  delay: { icon: <ClockCircleOutlined />, color: 'pink', label: '延时' },
  mcp: { icon: <CloudOutlined />, color: 'geekblue', label: 'MCP工具' },
}

const protocolMap: Record<string, string> = {
  http: 'HTTP',
  https: 'HTTPS',
  grpc: 'gRPC',
  graphql: 'GraphQL',
  soap: 'SOAP',
  websocket: 'WebSocket',
  postgresql: 'PostgreSQL',
  mysql: 'MySQL',
  mongodb: 'MongoDB',
  redis: 'Redis',
  kafka: 'Kafka',
  rabbitmq: 'RabbitMQ',
  mqtt: 'MQTT',
  python: 'Python',
  javascript: 'JavaScript',
  shell: 'Shell',
  openai: 'OpenAI',
  anthropic: 'Anthropic',
}

// 测试弹窗组件
interface TestModalProps {
  visible: boolean
  component: any
  onClose: () => void
}

const TestModal: React.FC<TestModalProps> = ({ visible, component, onClose }) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

  useEffect(() => {
    if (visible && component) {
      // 根据组件输入schema生成默认测试数据
      const defaultInput = generateDefaultInput(component.input_schema)
      form.setFieldsValue({ input_data: JSON.stringify(defaultInput, null, 2) })
      setResult(null)
    }
  }, [visible, component, form])

  const generateDefaultInput = (schema: any) => {
    if (!schema || !schema.properties) return {}
    const input: Record<string, any> = {}
    Object.entries(schema.properties).forEach(([key, prop]: [string, any]) => {
      switch (prop.type) {
        case 'string':
          input[key] = prop.example || ''
          break
        case 'number':
          input[key] = prop.example || 0
          break
        case 'boolean':
          input[key] = prop.example || false
          break
        case 'object':
          input[key] = prop.example || {}
          break
        case 'array':
          input[key] = prop.example || []
          break
        default:
          input[key] = null
      }
    })
    return input
  }

  const handleTest = async () => {
    try {
      setLoading(true)
      const values = await form.validateFields()
      const inputData = JSON.parse(values.input_data)
      const res = await post(`/components/${component.id}/test`, { input_data: inputData })
      setResult(res)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '测试失败')
    } finally {
      setLoading(false)
    }
  }

  if (!component) return null

  return (
    <Modal
      title={
        <Space>
          <PlayCircleOutlined style={{ color: '#1890ff' }} />
          <span>测试组件: {component.name}</span>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width={800}
      footer={[
        <Button key="close" onClick={onClose}>
          关闭
        </Button>,
        <Button key="test" type="primary" loading={loading} onClick={handleTest} icon={<PlayCircleOutlined />}>
          执行测试
        </Button>,
      ]}
    >
      <Spin spinning={loading}>
        <Form form={form} layout="vertical">
          <Form.Item
            name="input_data"
            label="输入数据 (JSON)"
            rules={[
              { required: true, message: '请输入输入数据' },
              {
                validator: (_, value) => {
                  try {
                    JSON.parse(value)
                    return Promise.resolve()
                  } catch {
                    return Promise.reject('请输入有效的JSON格式')
                  }
                },
              },
            ]}
          >
            <TextArea rows={8} style={{ fontFamily: 'monospace' }} />
          </Form.Item>
        </Form>

        {result && (
          <>
            <Divider />
            <div>
              <h4>测试结果</h4>
              <Tag color={result.success ? 'success' : 'error'}>
                {result.success ? '成功' : '失败'}
              </Tag>
              {result.duration_ms && (
                <Tag style={{ marginLeft: 8 }}>{result.duration_ms}ms</Tag>
              )}
              <TextArea
                rows={10}
                value={JSON.stringify(result.output_data || result, null, 2)}
                readOnly
                style={{ marginTop: 16, fontFamily: 'monospace', background: '#f5f5f5' }}
              />
              {result.logs && result.logs.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <h5>执行日志</h5>
                  <pre style={{ background: '#1e1e1e', color: '#d4d4d4', padding: 12, borderRadius: 4, fontSize: 12, maxHeight: 200, overflow: 'auto' }}>
                    {result.logs.join('\n')}
                  </pre>
                </div>
              )}
            </div>
          </>
        )}
      </Spin>
    </Modal>
  )
}

export const ComponentListPage = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [activeTab, setActiveTab] = useState('all')
  const [components, setComponents] = useState<any[]>([])
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  })
  const [testModalVisible, setTestModalVisible] = useState(false)
  const [currentTestComponent, setCurrentTestComponent] = useState<any>(null)

  useEffect(() => {
    fetchComponents()
  }, [pagination.current, pagination.pageSize, activeTab, searchText])

  const fetchComponents = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams({
        page: pagination.current.toString(),
        page_size: pagination.pageSize.toString(),
      })
      
      if (activeTab !== 'all') {
        params.append('component_type', activeTab)
      }
      
      if (searchText) {
        params.append('search', searchText)
      }
      
      const response: any = await get(`/components?${params}`)
      setComponents(response.data || [])
      setPagination(prev => ({ ...prev, total: response.total }))
    } catch (error) {
      message.error('获取组件列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => navigate('/components/new')
  const handleEdit = (id: string) => navigate(`/components/${id}`)
  
  const handleTest = (record: any) => {
    setCurrentTestComponent(record)
    setTestModalVisible(true)
  }
  
  const handleCloseTestModal = () => {
    setTestModalVisible(false)
    setCurrentTestComponent(null)
  }
  
  const handleDelete = async (id: string) => {
    try {
      await del(`/components/${id}`)
      message.success('组件已删除')
      fetchComponents()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败')
    }
  }

  const handlePublish = async (id: string) => {
    try {
      await post(`/components/${id}/publish`)
      message.success('组件已发布')
      fetchComponents()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '发布失败')
    }
  }

  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string, icon: any, text: string }> = {
      development: { color: 'default', icon: <ExclamationCircleOutlined />, text: '开发中' },
      testing: { color: 'warning', icon: <ThunderboltOutlined />, text: '测试中' },
      published: { color: 'success', icon: <CheckCircleOutlined />, text: '已发布' },
      deprecated: { color: 'error', icon: <ExclamationCircleOutlined />, text: '已废弃' },
    }
    const { color, icon, text } = statusMap[status] || { color: 'default', icon: null, text: status }
    return <Tag color={color} icon={icon}>{text}</Tag>
  }

  const getTypeTag = (type: string) => {
    const info = componentTypeMap[type] || { icon: <ApiOutlined />, color: 'default', label: type }
    return (
      <Tag color={info.color} icon={info.icon}>
        {info.label}
      </Tag>
    )
  }

  const columns = [
    {
      title: '组件信息',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: any) => (
        <div>
          <div style={{ fontWeight: 500, fontSize: 14 }}>
            {text}
            {record.status === 'published' && (
              <Badge status="success" style={{ marginLeft: 8 }} />
            )}
          </div>
          <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
            编码: {record.code}
            {record.execution_config?.protocol && (
              <Tag style={{ marginLeft: 8, fontSize: 12 }}>
                {protocolMap[record.execution_config.protocol] || record.execution_config.protocol}
              </Tag>
            )}
          </div>
          {record.description && (
            <div style={{ fontSize: 12, color: '#999', marginTop: 4, maxWidth: 300 }}>
              {record.description}
            </div>
          )}
        </div>
      ),
    },
    {
      title: '类型',
      dataIndex: 'component_type',
      key: 'component_type',
      width: 140,
      render: getTypeTag,
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      width: 80,
      render: (v: string) => <Tag style={{ fontSize: 12 }}>v{v}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: getStatusTag,
    },
    {
      title: '使用统计',
      key: 'stats',
      width: 120,
      render: (record: any) => (
        <div style={{ fontSize: 12, color: '#666' }}>
          <div>调用: {record.usage_count || 0}次</div>
          <div>评分: {record.rating || 5}⭐</div>
        </div>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (date: string) => date ? new Date(date).toLocaleString('zh-CN') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: any) => (
        <Space>
          <Tooltip title="测试">
            <Button
              type="text"
              icon={<PlayCircleOutlined style={{ color: '#1890ff' }} />}
              onClick={() => handleTest(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record.id)}
            />
          </Tooltip>
          <Dropdown
            menu={{
              items: [
                record.status !== 'published' && {
                  key: 'publish',
                  icon: <CheckCircleOutlined />,
                  label: '发布',
                  onClick: () => handlePublish(record.id),
                },
                {
                  key: 'delete',
                  icon: <DeleteOutlined />,
                  label: (
                    <Popconfirm
                      title="确定要删除这个组件吗？"
                      onConfirm={() => handleDelete(record.id)}
                      okText="确定"
                      cancelText="取消"
                    >
                      <span style={{ color: '#ff4d4f' }}>删除</span>
                    </Popconfirm>
                  ),
                },
              ].filter(Boolean) as any,
            }}
            placement="bottomRight"
          >
            <Button type="text" icon={<MoreOutlined />} />
          </Dropdown>
        </Space>
      ),
    },
  ]

  const tabItems = [
    { key: 'all', label: '全部', icon: <GlobalOutlined /> },
    { key: 'api', label: 'API服务', icon: <ApiOutlined /> },
    { key: 'database', label: '数据库', icon: <DatabaseOutlined /> },
    { key: 'message', label: '消息队列', icon: <NodeIndexOutlined /> },
    { key: 'script', label: '脚本', icon: <CodeOutlined /> },
    { key: 'ai', label: 'AI/LLM', icon: <RobotOutlined /> },
  ]

  return (
    <div className="component-list-page">
      <Card
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>组件管理</span>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
              注册组件
            </Button>
          </div>
        }
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems.map(item => ({
            key: item.key,
            label: (
              <span>
                {item.icon}
                <span style={{ marginLeft: 4 }}>{item.label}</span>
              </span>
            ),
          }))}
        />

        <div style={{ marginBottom: 16, display: 'flex', gap: 12 }}>
          <Search
            placeholder="搜索组件名称、编码"
            allowClear
            onSearch={setSearchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 300 }}
            prefix={<SearchOutlined />}
          />
        </div>

        <Table
          columns={columns}
          dataSource={components}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, pageSize) => {
              setPagination(prev => ({ current: page, pageSize: pageSize || 10, total: prev.total }))
            },
          }}
        />
      </Card>

      <TestModal
        visible={testModalVisible}
        component={currentTestComponent}
        onClose={handleCloseTestModal}
      />
    </div>
  )
}

export default ComponentListPage
