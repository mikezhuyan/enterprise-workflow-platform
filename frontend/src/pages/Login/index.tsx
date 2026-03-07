import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Form, Input, Button, Card, Typography, Space, message, Alert } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useAuthStore } from '../../stores/auth'
import './index.less'

const { Title, Text } = Typography

export const LoginPage = () => {
  const navigate = useNavigate()
  const { login, isLoading, error } = useAuthStore()
  const [form] = Form.useForm()
  const [localError, setLocalError] = useState<string | null>(null)

  const handleSubmit = async (values: { username: string; password: string }) => {
    console.log('表单提交:', values)
    setLocalError(null)
    
    try {
      const success = await login(values.username, values.password)
      console.log('登录结果:', success)
      
      if (success) {
        navigate('/', { replace: true })
      }
    } catch (err: any) {
      console.error('登录异常:', err)
      setLocalError(err.message || '登录发生错误')
    }
  }

  const handleFinishFailed = (errorInfo: any) => {
    console.log('表单验证失败:', errorInfo)
  }

  return (
    <div className="login-page">
      <div className="login-container">
        <Card className="login-card" bordered={false}>
          <Space direction="vertical" align="center" style={{ width: '100%' }}>
            <Title level={2} style={{ marginBottom: 8 }}>
              🔧 企业工作流平台
            </Title>
            <Text type="secondary" style={{ marginBottom: 32 }}>
              Enterprise Workflow Platform
            </Text>
          </Space>

          {(error || localError) && (
            <Alert
              message={error || localError}
              type="error"
              showIcon
              style={{ marginBottom: 16 }}
              closable
            />
          )}

          <Form
            form={form}
            name="login"
            onFinish={handleSubmit}
            onFinishFailed={handleFinishFailed}
            autoComplete="off"
            size="large"
          >
            <Form.Item
              name="username"
              rules={[{ required: true, message: '请输入用户名' }]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="用户名"
                autoFocus
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="密码"
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={isLoading}
                block
                size="large"
              >
                登录
              </Button>
            </Form.Item>
          </Form>

          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              默认账号: admin / admin123
            </Text>
          </div>
        </Card>
      </div>
    </div>
  )
}
