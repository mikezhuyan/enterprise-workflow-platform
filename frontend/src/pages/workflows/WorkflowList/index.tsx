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
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  MoreOutlined,
  PlayCircleOutlined,
  EditOutlined,
  DeleteOutlined,
  CopyOutlined,
  HistoryOutlined,
} from '@ant-design/icons'
import { get, post, del } from '../../../utils/request'

const { Search } = Input

interface Workflow {
  id: string
  name: string
  description?: string
  version: string
  status: string
  execution_count: number
  created_at: string
}

interface WorkflowListResponse {
  total: number
  page: number
  page_size: number
  pages: number
  data: Workflow[]
}

export const WorkflowListPage = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  })

  // 加载工作流列表
  const loadWorkflows = async (page: number = 1, pageSize: number = 10, search?: string) => {
    try {
      setLoading(true)
      const params: any = { page, page_size: pageSize }
      if (search) {
        params.search = search
      }
      
      const res: WorkflowListResponse = await get('/workflows', { params })
      if (res && res.data) {
        setWorkflows(res.data)
        setPagination({
          current: res.page,
          pageSize: res.page_size,
          total: res.total,
        })
      }
    } catch (error) {
      console.error('加载工作流列表失败:', error)
      message.error('加载工作流列表失败')
    } finally {
      setLoading(false)
    }
  }

  // 初始加载
  useEffect(() => {
    loadWorkflows()
  }, [])

  // 搜索
  const handleSearch = () => {
    loadWorkflows(1, pagination.pageSize, searchText)
  }

  // 分页变化
  const handleTableChange = (newPagination: any) => {
    loadWorkflows(newPagination.current, newPagination.pageSize, searchText)
  }

  const handleCreate = () => navigate('/workflows/new')
  const handleEdit = (id: string) => navigate(`/workflows/${id}`)
  const handleViewExecutions = (id: string) => navigate(`/workflows/${id}/executions`)
  
  const handleExecute = async (id: string) => {
    try {
      await post(`/workflows/${id}/execute`, { input_data: {} })
      message.success('开始执行工作流')
      // 刷新列表以更新执行次数
      loadWorkflows(pagination.current, pagination.pageSize, searchText)
    } catch (error: any) {
      console.error('执行失败:', error)
      message.error(error.response?.data?.detail || '执行失败')
    }
  }
  
  const handleDelete = async (id: string) => {
    try {
      await del(`/workflows/${id}`)
      message.success('工作流已删除')
      // 刷新列表
      loadWorkflows(pagination.current, pagination.pageSize, searchText)
    } catch (error: any) {
      console.error('删除失败:', error)
      message.error(error.response?.data?.detail || '删除失败')
    }
  }

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
          { 
            key: 'execute', 
            icon: <PlayCircleOutlined />, 
            label: '执行', 
            onClick: () => handleExecute(record.id) 
          },
          { 
            key: 'edit', 
            icon: <EditOutlined />, 
            label: '编辑', 
            onClick: () => handleEdit(record.id) 
          },
          { 
            key: 'executions', 
            icon: <HistoryOutlined />, 
            label: '执行记录', 
            onClick: () => handleViewExecutions(record.id) 
          },
          { 
            key: 'copy', 
            icon: <CopyOutlined />, 
            label: '复制',
            onClick: () => message.info('复制功能开发中'),
          },
          {
            key: 'delete',
            icon: <DeleteOutlined />,
            label: (
              <Popconfirm 
                title="确定要删除这个工作流吗？" 
                onConfirm={() => handleDelete(record.id)}
              >
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
            onSearch={handleSearch}
            style={{ width: 300 }}
          />
        </div>
        <Table
          columns={columns}
          dataSource={workflows}
          rowKey="id"
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showTotal: (total) => `共 ${total} 条`,
            showSizeChanger: true,
          }}
          onChange={handleTableChange}
        />
      </Card>
    </div>
  )
}
