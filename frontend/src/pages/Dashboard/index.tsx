import { useEffect, useState } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  List,
  Tag,
  Button,
  message,
} from 'antd'
import {
  ApiOutlined,
  AppstoreOutlined,
  CheckCircleOutlined,
  PlayCircleOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { get } from '../../services/request'
import './index.less'

interface DashboardStats {
  workflow_count: number
  component_count: number
  today_executions: number
  success_rate: number
}

interface RecentExecution {
  id: string
  name: string
  status: string
  time: string
}

export const DashboardPage = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<DashboardStats>({
    workflow_count: 0,
    component_count: 0,
    today_executions: 0,
    success_rate: 0,
  })
  const [recentExecutions, setRecentExecutions] = useState<RecentExecution[]>([])

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      setLoading(true)
      const res: any = await get('/dashboard/stats')
      if (res.success) {
        setStats(res.data)
        setRecentExecutions(res.data.recent_executions || [])
      }
    } catch (error) {
      message.error('获取统计数据失败')
    } finally {
      setLoading(false)
    }
  }

  const statsConfig = [
    {
      title: '工作流总数',
      value: stats.workflow_count,
      icon: <ApiOutlined />,
      color: '#1890ff',
    },
    {
      title: '组件总数',
      value: stats.component_count,
      icon: <AppstoreOutlined />,
      color: '#52c41a',
    },
    {
      title: '今日执行',
      value: stats.today_executions,
      icon: <PlayCircleOutlined />,
      color: '#722ed1',
    },
    {
      title: '成功率',
      value: stats.success_rate,
      suffix: '%',
      icon: <CheckCircleOutlined />,
      color: '#fa8c16',
    },
  ]

  const quickActions = [
    {
      title: '创建工作流',
      description: '设计新的业务流程',
      icon: <ApiOutlined />,
      action: () => navigate('/workflows/new'),
    },
    {
      title: '注册组件',
      description: '添加新的功能组件',
      icon: <AppstoreOutlined />,
      action: () => navigate('/components/new'),
    },
  ]

  return (
    <div className="dashboard-page">
      <Row gutter={[24, 24]}>
        {statsConfig.map((stat, index) => (
          <Col xs={24} sm={12} lg={6} key={index}>
            <Card loading={loading}>
              <Statistic
                title={stat.title}
                value={stat.value}
                suffix={stat.suffix}
                prefix={
                  <span style={{ color: stat.color, marginRight: 8 }}>
                    {stat.icon}
                  </span>
                }
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={16}>
          <Card title="快捷操作" loading={loading}>
            <Row gutter={[16, 16]}>
              {quickActions.map((action, index) => (
                <Col xs={24} sm={12} key={index}>
                  <Card
                    hoverable
                    className="quick-action-card"
                    onClick={action.action}
                  >
                    <div className="quick-action-content">
                      <div className="quick-action-icon">{action.icon}</div>
                      <div className="quick-action-text">
                        <div className="quick-action-title">{action.title}</div>
                        <div className="quick-action-desc">{action.description}</div>
                      </div>
                      <ArrowRightOutlined />
                    </div>
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card
            title="最近执行"
            loading={loading}
            extra={<Button type="link" onClick={() => navigate('/workflows')}>查看全部</Button>}
          >
            <List
              dataSource={recentExecutions}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    title={item.name}
                    description={item.time}
                  />
                  <Tag
                    color={
                      item.status === 'success'
                        ? 'success'
                        : item.status === 'failed'
                        ? 'error'
                        : 'processing'
                    }
                  >
                    {item.status === 'success'
                      ? '成功'
                      : item.status === 'failed'
                      ? '失败'
                      : '执行中'}
                  </Tag>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default DashboardPage
