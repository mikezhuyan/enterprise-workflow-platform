import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Button,
  Table,
  Tag,
  Space,
  message,
  Empty,
  Descriptions,
  Tabs,
} from 'antd'
import {
  ArrowLeftOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  EyeOutlined,
} from '@ant-design/icons'
import { get, post } from '../../../utils/request'
import type { TabsProps } from 'antd'

interface WorkflowExecution {
  id: string
  workflow_id: string
  status: string
  input_data?: any
  output_data?: any
  error_message?: string
  started_at?: string
  completed_at?: string
  duration_ms?: number
  triggered_by?: string
  trigger_type?: string
  created_at: string
}

interface Workflow {
  id: string
  name: string
  description?: string
  version: string
  status: string
  execution_count: number
}

export const ExecutionListPage = () => {
  const { id: workflowId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [executions, setExecutions] = useState<WorkflowExecution[]>([])
  const [workflow, setWorkflow] = useState<Workflow | null>(null)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  })

  // 加载工作流详情
  const loadWorkflow = async () => {
    if (!workflowId) return
    
    try {
      const res = await get(`/workflows/${workflowId}`)
      if (res) {
        setWorkflow(res)
      }
    } catch (error) {
      console.error('加载工作流详情失败:', error)
      message.error('加载工作流详情失败')
    }
  }

  // 加载执行记录列表
  const loadExecutions = async (page: number = 1, pageSize: number = 10) => {
    if (!workflowId) return
    
    try {
      setLoading(true)
      const params = { page, page_size: pageSize }
      const res = await get(`/workflows/${workflowId}/executions`, { params })
      if (res && res.data) {
        setExecutions(res.data)
        setPagination({
          current: res.page,
          pageSize: res.page_size,
          total: res.total,
        })
      }
    } catch (error) {
      console.error('加载执行记录失败:', error)
      message.error('加载执行记录失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadWorkflow()
    loadExecutions()
  }, [workflowId])

  // 返回工作流列表
  const handleBack = () => {
    navigate('/workflows')
  }

  // 查看执行详情
  const handleViewDetail = (executionId: string) => {
    navigate(`/workflows/${workflowId}/executions/${executionId}`)
  }

  // 执行工作流
  const handleExecute = async () => {
    if (!workflowId) return
    
    try {
      await post(`/workflows/${workflowId}/execute`, { input_data: {} })
      message.success('开始执行工作流')
      // 刷新列表
      loadExecutions(pagination.current, pagination.pageSize)
      loadWorkflow()
    } catch (error: any) {
      console.error('执行失败:', error)
      message.error(error.response?.data?.detail || '执行失败')
    }
  }

  // 分页变化
  const handleTableChange = (newPagination: any) => {
    loadExecutions(newPagination.current, newPagination.pageSize)
  }

  // 获取状态标签
  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; icon: React.ReactNode; text: string }> = {
      pending: { color: 'default', icon: <ClockCircleOutlined />, text: '待执行' },
      running: { color: 'processing', icon: <PlayCircleOutlined />, text: '执行中' },
      success: { color: 'success', icon: <CheckCircleOutlined />, text: '成功' },
      failed: { color: 'error', icon: <CloseCircleOutlined />, text: '失败' },
      cancelled: { color: 'warning', icon: <CloseCircleOutlined />, text: '已取消' },
    }
    const { color, icon, text } = statusMap[status] || { color: 'default', icon: null, text: status }
    return (
      <Tag color={color} icon={icon}>
        {text}
      </Tag>
    )
  }

  // 表格列
  const columns = [
    {
      title: '执行ID',
      dataIndex: 'id',
      key: 'id',
      width: 220,
      render: (id: string) => <span style={{ fontFamily: 'monospace', fontSize: 12 }}>{id}</span>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => getStatusTag(status),
    },
    {
      title: '触发方式',
      dataIndex: 'trigger_type',
      key: 'trigger_type',
      width: 100,
      render: (type: string) => type === 'manual' ? '手动' : type,
    },
    {
      title: '耗时',
      dataIndex: 'duration_ms',
      key: 'duration_ms',
      width: 100,
      render: (ms?: number) => {
        if (!ms) return '-'
        if (ms < 1000) return `${ms}ms`
        return `${(ms / 1000).toFixed(2)}s`
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '开始时间',
      dataIndex: 'started_at',
      key: 'started_at',
      width: 180,
      render: (date?: string) => date ? new Date(date).toLocaleString('zh-CN') : '-',
    },
    {
      title: '结束时间',
      dataIndex: 'completed_at',
      key: 'completed_at',
      width: 180,
      render: (date?: string) => date ? new Date(date).toLocaleString('zh-CN') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      fixed: 'right' as const,
      render: (_: any, record: WorkflowExecution) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => handleViewDetail(record.id)}
        >
          详情
        </Button>
      ),
    },
  ]

  // 统计信息
  const getStats = () => {
    const total = executions.length
    const success = executions.filter(e => e.status === 'success').length
    const failed = executions.filter(e => e.status === 'failed').length
    const running = executions.filter(e => e.status === 'running').length
    
    return { total, success, failed, running }
  }

  const stats = getStats()

  // Tab 项目
  const tabItems: TabsProps['items'] = [
    {
      key: 'list',
      label: '执行记录',
      children: (
        <Table
          columns={columns}
          dataSource={executions}
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
          scroll={{ x: 1200 }}
        />
      ),
    },
  ]

  if (!workflowId) {
    return <Empty description="无效的工作流ID" />
  }

  return (
    <div className="execution-list-page" style={{ padding: 24 }}>
      <Card
        title={
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={handleBack}>
              返回
            </Button>
            <span>工作流执行记录</span>
            {workflow && <Tag>{workflow.name}</Tag>}
          </Space>
        }
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={() => loadExecutions()}>
              刷新
            </Button>
            <Button type="primary" icon={<PlayCircleOutlined />} onClick={handleExecute}>
              执行工作流
            </Button>
          </Space>
        }
      >
        {workflow && (
          <Descriptions title="工作流信息" bordered column={3} style={{ marginBottom: 24 }}>
            <Descriptions.Item label="名称">{workflow.name}</Descriptions.Item>
            <Descriptions.Item label="版本">{workflow.version}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={workflow.status === 'published' ? 'success' : 'default'}>
                {workflow.status === 'published' ? '已发布' : '草稿'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="总执行次数">{workflow.execution_count}</Descriptions.Item>
            <Descriptions.Item label="成功次数">{stats.success}</Descriptions.Item>
            <Descriptions.Item label="失败次数">{stats.failed}</Descriptions.Item>
          </Descriptions>
        )}

        <Tabs items={tabItems} defaultActiveKey="list" />
      </Card>
    </div>
  )
}
