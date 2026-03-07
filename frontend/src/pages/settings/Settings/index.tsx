import { useState } from 'react'
import {
  Card,
  Form,
  Input,
  Button,
  Tabs,
  Switch,
  Slider,
  message,
} from 'antd'
import {
  SaveOutlined,
  SettingOutlined,
  SafetyOutlined,
  BellOutlined,
  ApiOutlined,
} from '@ant-design/icons'

const { TabPane } = Tabs

export const SettingsPage = () => {
  const [form] = Form.useForm()

  const handleSave = () => {
    message.success('设置已保存')
  }

  return (
    <div className="settings-page">
      <Card title="系统设置">
        <Tabs defaultActiveKey="general">
          <TabPane
            tab={<><SettingOutlined /> 通用设置</>}
            key="general"
          >
            <Form
              form={form}
              layout="vertical"
              style={{ maxWidth: 600 }}
            >
              <Form.Item name="site_name" label="站点名称">
                <Input placeholder="企业工作流平台" />
              </Form.Item>
              <Form.Item name="logo" label="Logo">
                <Input placeholder="Logo URL" />
              </Form.Item>
              <Form.Item name="footer" label="页脚信息">
                <Input placeholder="页脚版权信息" />
              </Form.Item>
              <Form.Item>
                <Button type="primary" icon={<SaveOutlined />} onClick={handleSave}>
                  保存设置
                </Button>
              </Form.Item>
            </Form>
          </TabPane>

          <TabPane
            tab={<><SafetyOutlined /> 安全设置</>}
            key="security"
          >
            <Form layout="vertical" style={{ maxWidth: 600 }}>
              <Form.Item label="密码最小长度">
                <Slider min={6} max={20} defaultValue={8} marks={{ 6: '6', 12: '12', 20: '20' }} />
              </Form.Item>
              <Form.Item label="登录失败锁定">
                <Switch defaultChecked />
              </Form.Item>
              <Form.Item label="Token过期时间(小时)">
                <Slider min={1} max={24} defaultValue={8} />
              </Form.Item>
              <Form.Item>
                <Button type="primary" icon={<SaveOutlined />} onClick={handleSave}>
                  保存设置
                </Button>
              </Form.Item>
            </Form>
          </TabPane>

          <TabPane
            tab={<><ApiOutlined /> MCP设置</>}
            key="mcp"
          >
            <Form layout="vertical" style={{ maxWidth: 600 }}>
              <Form.Item label="启用MCP">
                <Switch defaultChecked />
              </Form.Item>
              <Form.Item label="MCP超时时间(秒)">
                <Slider min={5} max={120} defaultValue={30} />
              </Form.Item>
              <Form.Item>
                <Button type="primary" icon={<SaveOutlined />} onClick={handleSave}>
                  保存设置
                </Button>
              </Form.Item>
            </Form>
          </TabPane>

          <TabPane
            tab={<><BellOutlined /> 通知设置</>}
            key="notifications"
          >
            <Form layout="vertical" style={{ maxWidth: 600 }}>
              <Form.Item label="工作流执行失败通知">
                <Switch defaultChecked />
              </Form.Item>
              <Form.Item label="系统告警通知">
                <Switch defaultChecked />
              </Form.Item>
              <Form.Item label="每日统计报告">
                <Switch />
              </Form.Item>
              <Form.Item>
                <Button type="primary" icon={<SaveOutlined />} onClick={handleSave}>
                  保存设置
                </Button>
              </Form.Item>
            </Form>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}
