import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Button,
  Tag,
  Timeline,
  Spin,
  Empty,
  Descriptions,
  Tabs,
  Table,
  message,
  Space,
} from 'antd'
import {
  ArrowLeftOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import { get } from '../../../utils/request'
import type { TabsProps } from 'antd'

interface NodeExecution {
  id: string
  node_id: string
  node_type: string
  node_name?: string
  status: string
  input_data?: any
  output_data?: any
  error_message?: string
  started_at?: string
  completed_at?: string
  duration_ms?: number
}

interface WorkflowExecution {
  id: string
  workflow_id: string
  status: string
  input_data?: any
  output_data?: any
  error_message?: string
  context?: any
  started_at?: string
  completed_at?: string
  duration_ms?: number
  triggered_by?: string
  trigger_type?: string
  created_at: string
  node_executions?: NodeExecution[]
}

export const ExecutionDetailPage = () => {
  const { workflowId, executionId } = useParams<{ workflowId: string; executionId: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [execution, setExecution] = useState<WorkflowExecution | null>(null)

  // 加载执行详情
  const loadExecution = async () => {
    if (!executionId) return
    
    try {
      setLoading(true)
      const res = await get(`/workflows/executions/${executionId}`)
      if (res) {
        setExecution(res)
      }
    } catch (error) {
      console.error('加载执行详情失败:', error)
      message.error('加载执行详情失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadExecution()
  }, [executionId])

  // 返回工作流详情
  const handleBack = () => {
    if (workflowId) {
      navigate(`/workflows/${workflowId}`)
    } else {
      navigate('/workflows')
    }
  }

  // 返回工作流列表
  const handleBackToList = () => {
    navigate('/workflows')
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

  // 节点执行表格列
  const nodeExecutionColumns = [
    {
      title: '节点名称',
      dataIndex: 'node_name',
      key: 'node_name',
      render: (name: string, record: any) => name || record.node_id,
    },
    {
      title: '节点ID',
      dataIndex: 'node_id',
      key: 'node_id',
      render: (id: string) => <span style={{ fontFamily: 'monospace', fontSize: 12 }}>{id.substring(0, 8)}...</span>,
    },
    {
      title: '节点类型',
      dataIndex: 'node_type',
      key: 'node_type',
      width: 100,
      render: (type: string) => (
        <Tag>{type}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => getStatusTag(status),
    },
    {
      title: '耗时(ms)',
      dataIndex: 'duration_ms',
      key: 'duration_ms',
      render: (ms?: number) => ms ? `${ms}ms` : '-',
    },
    {
      title: '开始时间',
      dataIndex: 'started_at',
      key: 'started_at',
      render: (date?: string) => date ? new Date(date).toLocaleString('zh-CN') : '-',
    },
    {
      title: '结束时间',
      dataIndex: 'completed_at',
      key: 'completed_at',
      render: (date?: string) => date ? new Date(date).toLocaleString('zh-CN') : '-',
    },
  ]

  // 渲染时间线
  const renderTimeline = () => {
    if (!execution?.node_executions || execution.node_executions.length === 0) {
      return <Empty description="暂无节点执行记录" />
    }

    return (
      <Timeline mode="left">
        {execution.node_executions.map((node) => (
          <Timeline.Item
            key={node.id}
            color={
              node.status === 'success'
                ? 'green'
                : node.status === 'failed'
                ? 'red'
                : node.status === 'running'
                ? 'blue'
                : 'gray'
            }
            label={
              <Space direction="vertical" size={0} style={{ textAlign: 'right' }}>
                <span>{node.node_type}</span>
                {node.duration_ms && <span style={{ fontSize: 12, color: '#999' }}>{node.duration_ms}ms</span>}
              </Space>
            }
          >
            <Card size="small" style={{ marginBottom: 8 }}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Space>
                  <strong>{node.node_name || node.node_id}</strong>
                  {getStatusTag(node.status)}
                </Space>
                
                {node.input_data && (
                  <div>
                    <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>输入:</div>
                    <pre style={{ 
                      background: '#f5f5f5', 
                      padding: 8, 
                      borderRadius: 4,
                      fontSize: 12,
                      maxHeight: 150,
                      overflow: 'auto',
                      margin: 0
                    }}>
                      {JSON.stringify(node.input_data, null, 2)}
                    </pre>
                  </div>
                )}
                
                {node.output_data && (
                  <div>
                    <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>输出:</div>
                    <pre style={{ 
                      background: '#f0f8ff', 
                      padding: 8, 
                      borderRadius: 4,
                      fontSize: 12,
                      maxHeight: 200,
                      overflow: 'auto',
                      margin: 0
                    }}>
                      {JSON.stringify(node.output_data, null, 2)}
                    </pre>
                  </div>
                )}
                
                {node.error_message && (
                  <div>
                    <div style={{ fontSize: 12, color: '#ff4d4f', marginBottom: 4 }}>错误:</div>
                    <pre style={{ 
                      background: '#fff1f0', 
                      padding: 8, 
                      borderRadius: 4,
                      fontSize: 12,
                      color: '#ff4d4f',
                      maxHeight: 150,
                      overflow: 'auto',
                      margin: 0
                    }}>
                      {node.error_message}
                    </pre>
                  </div>
                )}
              </Space>
            </Card>
          </Timeline.Item>
        ))}
      </Timeline>
    )
  }

  // Tab 项目
  const tabItems: TabsProps['items'] = [
    {
      key: 'overview',
      label: '执行概览',
      children: (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Descriptions title="基本信息" bordered column={2}>
            <Descriptions.Item label="执行ID">{execution?.id}</Descriptions.Item>
            <Descriptions.Item label="工作流ID">
              <a onClick={handleBack}>{execution?.workflow_id}</a>
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              {getStatusTag(execution?.status || 'unknown')}
            </Descriptions.Item>
            <Descriptions.Item label="触发方式">
              {execution?.trigger_type === 'manual' ? '手动' : execution?.trigger_type}
            </Descriptions.Item>
            <Descriptions.Item label="总耗时">
              {execution?.duration_ms ? `${execution.duration_ms}ms` : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {execution?.created_at ? new Date(execution.created_at).toLocaleString('zh-CN') : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="开始时间">
              {execution?.started_at ? new Date(execution.started_at).toLocaleString('zh-CN') : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="结束时间">
              {execution?.completed_at ? new Date(execution.completed_at).toLocaleString('zh-CN') : '-'}
            </Descriptions.Item>
          </Descriptions>

          {execution?.input_data && (
            <Card title="输入数据" size="small">
              <pre style={{ 
                background: '#f5f5f5', 
                padding: 12, 
                borderRadius: 4,
                fontSize: 12,
                maxHeight: 300,
                overflow: 'auto',
                margin: 0
              }}>
                {JSON.stringify(execution.input_data, null, 2)}
              </pre>
            </Card>
          )}

          {execution?.output_data && (
            <Card title="输出结果" size="small">
              <pre style={{ 
                background: '#f0f8ff', 
                padding: 12, 
                borderRadius: 4,
                fontSize: 12,
                maxHeight: 400,
                overflow: 'auto',
                margin: 0
              }}>
                {JSON.stringify(execution.output_data, null, 2)}
              </pre>
            </Card>
          )}

          {execution?.error_message && (
            <Card title="错误信息" size="small" style={{ borderColor: '#ff4d4f' }}>
              <pre style={{ 
                background: '#fff1f0', 
                padding: 12, 
                borderRadius: 4,
                fontSize: 12,
                color: '#ff4d4f',
                maxHeight: 300,
                overflow: 'auto',
                margin: 0
              }}>
                {execution.error_message}
              </pre>
            </Card>
          )}
        </Space>
      ),
    },
    {
      key: 'nodes',
      label: '节点执行',
      children: (
        <Table
          columns={nodeExecutionColumns}
          dataSource={execution?.node_executions || []}
          rowKey="id"
          pagination={false}
        />
      ),
    },
    {
      key: 'timeline',
      label: '执行时间线',
      children: renderTimeline(),
    },
  ]

  if (loading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Spin size="large" />
        <p>加载中...</p>
      </div>
    )
  }

  if (!execution) {
    return (
      <div style={{ padding: 24 }}>
        <Empty description="执行记录不存在" />
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Button onClick={handleBackToList}>返回列表</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="execution-detail-page" style={{ padding: 24 }}>
      <Card
        title={
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={handleBack}>
              返回
            </Button>
            <span>执行详情</span>
            {getStatusTag(execution.status)}
          </Space>
        }
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={loadExecution}>
              刷新
            </Button>
          </Space>
        }
      >
        <Tabs items={tabItems} defaultActiveKey="overview" />
      </Card>
    </div>
  )
}
