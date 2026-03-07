import { useState } from 'react'
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
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  MoreOutlined,
  PlayCircleOutlined,
  EditOutlined,
  DeleteOutlined,
  CopyOutlined,
} from '@ant-design/icons'

const { Search } = Input

const mockWorkflows = [
  {
    id: '1',
    name: '订单处理流程',
    description: '自动处理新订单，包括库存检查、支付验证和发货通知',
    version: '1.2.0',
    status: 'published',
    execution_count: 1256,
    created_at: '2024-01-15T08:30:00Z',
  },
  {
    id: '2',
    name: '数据同步任务',
    description: '定时同步多个数据源的订单数据到数据仓库',
    version: '2.0.0',
    status: 'published',
    execution_count: 3420,
    created_at: '2024-01-10T14:20:00Z',
  },
  {
    id: '3',
    name: '客户关怀流程',
    description: '根据客户行为触发自动化的关怀邮件和优惠券发送',
    version: '1.0.0',
    status: 'draft',
    execution_count: 0,
    created_at: '2024-01-20T09:15:00Z',
  },
]

export const WorkflowListPage = () => {
  const navigate = useNavigate()
  const [loading] = useState(false)
  const [searchText, setSearchText] = useState('')

  const handleCreate = () => navigate('/workflows/new')
  const handleEdit = (id: string) => navigate(`/workflows/${id}`)
  const handleExecute = () => message.success('开始执行工作流')
  const handleDelete = () => message.success('工作流已删除')

  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; text: string }> = {
      draft: { color: 'default', text: '草稿' },
      published: { color: 'success', text: '已发布' },
      archived: { color: 'warning', text: '已归档' },
      disabled: { color: 'error', text: '已禁用' },
    }
    const { color, text } = statusMap[status] || { color: 'default', text: status }
    return <Tag color={color}>{text}</Tag>
  }

  const columns = [
    {
      title: '工作流名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: any) => (
        <div>
          <div style={{ fontWeight: 500 }}>{text}</div>
          <div style={{ fontSize: 12, color: '#666' }}>{record.description}</div>
        </div>
      ),
    },
    { title: '版本', dataIndex: 'version', key: 'version', width: 100 },
    { title: '状态', dataIndex: 'status', key: 'status', width: 100, render: getStatusTag },
    { title: '执行次数', dataIndex: 'execution_count', key: 'execution_count', width: 120 },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, record: any) => {
        const items = [
          { key: 'execute', icon: <PlayCircleOutlined />, label: '执行', onClick: handleExecute },
          { key: 'edit', icon: <EditOutlined />, label: '编辑', onClick: () => handleEdit(record.id) },
          { key: 'copy', icon: <CopyOutlined />, label: '复制' },
          {
            key: 'delete',
            icon: <DeleteOutlined />,
            label: (
              <Popconfirm title="确定要删除这个工作流吗？" onConfirm={handleDelete}>
                <span style={{ color: '#ff4d4f' }}>删除</span>
              </Popconfirm>
            ),
          },
        ]
        return (
          <Dropdown menu={{ items }} placement="bottomRight">
            <Button type="text" icon={<MoreOutlined />} />
          </Dropdown>
        )
      },
    },
  ]

  return (
    <div className="workflow-list-page">
      <Card
        title="工作流管理"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            创建工作流
          </Button>
        }
      >
        <div style={{ marginBottom: 16 }}>
          <Search
            placeholder="搜索工作流名称"
            allowClear
            enterButton={<><SearchOutlined /> 搜索</>}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 300 }}
          />
        </div>
        <Table
          columns={columns}
          dataSource={mockWorkflows}
          rowKey="id"
          loading={loading}
          pagination={{ total: mockWorkflows.length, pageSize: 10, showTotal: (total) => `共 ${total} 条` }}
        />
      </Card>
    </div>
  )
}
