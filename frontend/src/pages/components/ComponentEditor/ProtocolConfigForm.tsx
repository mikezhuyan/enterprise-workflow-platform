import React from 'react'
import { Form, Input, Select, InputNumber, Switch, Row, Col, Alert } from 'antd'

const { TextArea } = Input
const { Option } = Select

interface ProtocolConfigFormProps {
  protocol: string
  executionConfig: any
  onChange: (config: any) => void
}

export const ProtocolConfigForm: React.FC<ProtocolConfigFormProps> = ({
  protocol,
  executionConfig,
  onChange,
}) => {
  const commonProps = { style: { marginBottom: 16 } }

  const handleChange = (key: string, value: any) => {
    onChange({ ...executionConfig, [key]: value })
  }

  switch (protocol) {
    case 'http':
    case 'https':
      return (
        <>
          <Form.Item label="请求方法" {...commonProps}>
            <Select value={executionConfig.method} onChange={v => handleChange('method', v)}>
              <Option value="GET">GET</Option>
              <Option value="POST">POST</Option>
              <Option value="PUT">PUT</Option>
              <Option value="DELETE">DELETE</Option>
              <Option value="PATCH">PATCH</Option>
            </Select>
          </Form.Item>
          <Form.Item label="请求URL" {...commonProps}>
            <Input 
              value={executionConfig.url} 
              onChange={e => handleChange('url', e.target.value)} 
              placeholder="https://api.example.com/endpoint" 
            />
          </Form.Item>
          <Form.Item label="请求头 (JSON)" {...commonProps}>
            <TextArea 
              rows={3} 
              value={JSON.stringify(executionConfig.headers || {}, null, 2)} 
              onChange={e => {
                try { handleChange('headers', JSON.parse(e.target.value)) } catch {}
              }} 
            />
          </Form.Item>
          <Form.Item label="查询参数 (JSON)" {...commonProps}>
            <TextArea 
              rows={2} 
              value={JSON.stringify(executionConfig.params || {}, null, 2)} 
              onChange={e => {
                try { handleChange('params', JSON.parse(e.target.value)) } catch {}
              }} 
            />
          </Form.Item>
          {(executionConfig.method === 'POST' || executionConfig.method === 'PUT' || executionConfig.method === 'PATCH') && (
            <Form.Item label="请求体 (JSON)" {...commonProps}>
              <TextArea 
                rows={6} 
                value={executionConfig.body} 
                onChange={e => handleChange('body', e.target.value)} 
              />
            </Form.Item>
          )}
          <Form.Item label="超时时间(秒)">
            <InputNumber 
              value={executionConfig.timeout} 
              onChange={v => handleChange('timeout', v)} 
              min={1} 
              max={300} 
            />
          </Form.Item>
          <Form.Item>
            <Switch 
              checked={executionConfig.verify_ssl} 
              onChange={v => handleChange('verify_ssl', v)} 
            /> 验证SSL证书
          </Form.Item>
        </>
      )

    case 'graphql':
      return (
        <>
          <Form.Item label="GraphQL端点" {...commonProps}>
            <Input 
              value={executionConfig.url} 
              onChange={e => handleChange('url', e.target.value)} 
              placeholder="https://api.example.com/graphql" 
            />
          </Form.Item>
          <Form.Item label="查询语句" {...commonProps}>
            <TextArea 
              rows={10} 
              value={executionConfig.query} 
              onChange={e => handleChange('query', e.target.value)} 
            />
          </Form.Item>
          <Form.Item label="变量 (JSON)" {...commonProps}>
            <TextArea 
              rows={4} 
              value={JSON.stringify(executionConfig.variables || {}, null, 2)} 
              onChange={e => {
                try { handleChange('variables', JSON.parse(e.target.value)) } catch {}
              }} 
            />
          </Form.Item>
        </>
      )

    case 'soap':
      return (
        <>
          <Form.Item label="SOAP地址" {...commonProps}>
            <Input value={executionConfig.url} onChange={e => handleChange('url', e.target.value)} />
          </Form.Item>
          <Form.Item label="SOAP Action" {...commonProps}>
            <Input value={executionConfig.soap_action} onChange={e => handleChange('soap_action', e.target.value)} />
          </Form.Item>
          <Form.Item label="SOAP Body (XML)" {...commonProps}>
            <TextArea rows={10} value={executionConfig.body} onChange={e => handleChange('body', e.target.value)} />
          </Form.Item>
        </>
      )

    case 'postgresql':
    case 'mysql':
      return (
        <>
          <Form.Item label="连接字符串" {...commonProps}>
            <Input 
              value={executionConfig.connection_string} 
              onChange={e => handleChange('connection_string', e.target.value)} 
              placeholder={`${protocol}://user:pass@localhost:5432/dbname`} 
            />
          </Form.Item>
          <Form.Item label="SQL语句" {...commonProps}>
            <TextArea 
              rows={8} 
              value={executionConfig.sql} 
              onChange={e => handleChange('sql', e.target.value)} 
              placeholder="SELECT * FROM users WHERE id = {{userId}}" 
            />
          </Form.Item>
          <Alert message="提示: 使用 {{变量名}} 语法引用输入参数" type="info" showIcon style={{ marginBottom: 16 }} />
        </>
      )

    case 'mongodb':
      return (
        <>
          <Form.Item label="连接字符串" {...commonProps}>
            <Input value={executionConfig.connection_string} onChange={e => handleChange('connection_string', e.target.value)} />
          </Form.Item>
          <Form.Item label="集合名称" {...commonProps}>
            <Input value={executionConfig.collection} onChange={e => handleChange('collection', e.target.value)} />
          </Form.Item>
          <Form.Item label="操作类型" {...commonProps}>
            <Select value={executionConfig.operation} onChange={v => handleChange('operation', v)}>
              <Option value="find">查询 (find)</Option>
              <Option value="insert">插入 (insert)</Option>
              <Option value="update">更新 (update)</Option>
              <Option value="delete">删除 (delete)</Option>
            </Select>
          </Form.Item>
          <Form.Item label="查询条件/数据 (JSON)" {...commonProps}>
            <TextArea rows={6} value={executionConfig.filter} onChange={e => handleChange('filter', e.target.value)} />
          </Form.Item>
        </>
      )

    case 'kafka':
      return (
        <>
          <Form.Item label="Broker地址" {...commonProps}>
            <Input value={executionConfig.brokers} onChange={e => handleChange('brokers', e.target.value)} placeholder="localhost:9092" />
          </Form.Item>
          <Form.Item label="Topic" {...commonProps}>
            <Input value={executionConfig.topic} onChange={e => handleChange('topic', e.target.value)} />
          </Form.Item>
          <Form.Item label="消息Key" {...commonProps}>
            <Input value={executionConfig.key} onChange={e => handleChange('key', e.target.value)} />
          </Form.Item>
          <Form.Item label="消息内容 (JSON)" {...commonProps}>
            <TextArea rows={6} value={executionConfig.message} onChange={e => handleChange('message', e.target.value)} />
          </Form.Item>
        </>
      )

    case 'python':
    case 'javascript':
      return (
        <>
          <Form.Item label={`${protocol === 'python' ? 'Python' : 'JavaScript'} 代码`} {...commonProps}>
            <TextArea 
              rows={20} 
              value={executionConfig.code} 
              onChange={e => handleChange('code', e.target.value)} 
              style={{ fontFamily: 'monospace' }} 
            />
          </Form.Item>
          <Alert message="提示: 输入数据可通过 input_data 变量访问" type="info" showIcon />
        </>
      )

    case 'openai':
      return (
        <>
          <Form.Item label="模型" {...commonProps}>
            <Select value={executionConfig.model} onChange={v => handleChange('model', v)}>
              <Option value="gpt-4">GPT-4</Option>
              <Option value="gpt-4-turbo">GPT-4 Turbo</Option>
              <Option value="gpt-3.5-turbo">GPT-3.5 Turbo</Option>
            </Select>
          </Form.Item>
          <Form.Item label="API Key" {...commonProps}>
            <Input.Password value={executionConfig.api_key} onChange={e => handleChange('api_key', e.target.value)} placeholder="sk-..." />
          </Form.Item>
          <Form.Item label="系统提示词" {...commonProps}>
            <TextArea rows={3} value={executionConfig.system_prompt} onChange={e => handleChange('system_prompt', e.target.value)} />
          </Form.Item>
          <Form.Item label="用户提示词" {...commonProps}>
            <TextArea rows={4} value={executionConfig.user_prompt} onChange={e => handleChange('user_prompt', e.target.value)} placeholder="使用 {{变量名}} 引用输入参数" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Temperature">
                <InputNumber value={executionConfig.temperature} onChange={v => handleChange('temperature', v)} min={0} max={2} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="最大Token">
                <InputNumber value={executionConfig.max_tokens} onChange={v => handleChange('max_tokens', v)} min={1} max={4000} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        </>
      )

    default:
      return (
        <Alert message={`${protocol} 协议配置开发中...`} type="warning" showIcon />
      )
  }
}

export default ProtocolConfigForm
