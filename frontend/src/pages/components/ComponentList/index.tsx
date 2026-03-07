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
} from '@ant-design/icons'
import { get, del, post } from '../../../services/request'

const { Search } = Input
const { Option } = Select
const { TabPane } = Tabs

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
  
  const handleTest = async (record: any) => {
    navigate(`/components/${record.id}`)
    // 可以在这里添加自动打开测试弹窗的逻辑
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
      width: 80,
      render: (_: any, record: any) => {
        const items = [
          {
            key: 'test',
            icon: <PlayCircleOutlined />,
            label: '测试',
            onClick: () => handleTest(record),
          },
          {
            key: 'edit',
            icon: <EditOutlined />,
            label: '编辑',
            onClick: () => handleEdit(record.id),
          },
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
        ].filter((item): item is { key: string; icon: any; label: any; onClick?: () => void } => Boolean(item))

        return (
          <Dropdown menu={{ items }} placement="bottomRight">
            <Button type="text" icon={<MoreOutlined />} />
          </Dropdown>
        )
      },
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
          <Space>
            <span>组件管理</span>
            <Tooltip title="组件是可复用的功能单元，支持多种微服务协议">
              <ExclamationCircleOutlined style={{ color: '#999' }} />
            </Tooltip>
          </Space>
        }
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            注册组件
          </Button>
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
            placeholder="搜索组件名称、编码或描述"
            allowClear
            enterButton={<><SearchOutlined /> 搜索</>}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            onSearch={() => fetchComponents()}
            style={{ width: 350 }}
          />
          <Select
            placeholder="选择状态"
            style={{ width: 120 }}
            allowClear
            onChange={(v) => {
              // 可以添加状态筛选逻辑
            }}
          >
            <Option value="development">开发中</Option>
            <Option value="testing">测试中</Option>
            <Option value="published">已发布</Option>
          </Select>
        </div>

        <Table
          columns={columns}
          dataSource={components}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 个组件`,
            onChange: (page, pageSize) => {
              setPagination({ ...pagination, current: page, pageSize })
            },
          }}
        />
      </Card>
    </div>
  )
}

export default ComponentListPage
