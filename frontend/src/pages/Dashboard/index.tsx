import { useEffect, useState } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Timeline,
  List,
  Tag,
  Button,
} from 'antd'
import {
  ApiOutlined,
  AppstoreOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  PlayCircleOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import './index.less'

export const DashboardPage = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // 模拟数据加载
    const timer = setTimeout(() => setLoading(false), 500)
    return () => clearTimeout(timer)
  }, [])

  const stats = [
    {
      title: '工作流总数',
      value: 42,
      icon: <ApiOutlined />,
      color: '#1890ff',
    },
    {
      title: '组件总数',
      value: 128,
      icon: <AppstoreOutlined />,
      color: '#52c41a',
    },
    {
      title: '今日执行',
      value: 256,
      icon: <PlayCircleOutlined />,
      color: '#722ed1',
    },
    {
      title: '成功率',
      value: 98.5,
      suffix: '%',
      icon: <CheckCircleOutlined />,
      color: '#fa8c16',
    },
  ]

  const recentExecutions = [
    { id: 1, name: '订单处理流程', status: 'success', time: '2分钟前' },
    { id: 2, name: '数据同步任务', status: 'running', time: '5分钟前' },
    { id: 3, name: '报表生成', status: 'success', time: '10分钟前' },
    { id: 4, name: '邮件发送', status: 'failed', time: '15分钟前' },
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
        {stats.map((stat, index) => (
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
          <Card
            title="快捷操作"
            loading={loading}
          >
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
            extra={<Button type="link">查看全部</Button>}
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
