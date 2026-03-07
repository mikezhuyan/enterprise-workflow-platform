import React, { useState, useEffect } from 'react';
import {
  Form,
  Input,
  Select,
  InputNumber,
  Switch,
  Button,
  Space,
  Divider,
  Alert,
  Card,
  Tag,
  Row,
  Col,
} from 'antd';
import {
  DeleteOutlined,
  PlusOutlined,
  ApiOutlined,
  DatabaseOutlined,
  RobotOutlined,
  CloudOutlined,
  BranchesOutlined,
  CodeOutlined,
  MailOutlined,
} from '@ant-design/icons';
import { ConfigField, getNodeTypeDefinition } from '../types/nodeTypes';
import type { Component } from '../../../../types/component';

const { TextArea } = Input;
const { Option } = Select;

interface NodeConfigPanelProps {
  node: any;
  components: Component[];
  onSave: (nodeId: string, config: any) => void;
  onDelete: (nodeId: string) => void;
}

// 获取图标组件
const getIcon = (iconName: string, color: string) => {
  const iconStyle = { fontSize: 18, color };
  switch (iconName) {
    case 'ApiOutlined':
      return <ApiOutlined style={iconStyle} />;
    case 'DatabaseOutlined':
      return <DatabaseOutlined style={iconStyle} />;
    case 'RobotOutlined':
      return <RobotOutlined style={iconStyle} />;
    case 'CloudOutlined':
      return <CloudOutlined style={iconStyle} />;
    case 'BranchesOutlined':
      return <BranchesOutlined style={iconStyle} />;
    case 'CodeOutlined':
      return <CodeOutlined style={iconStyle} />;
    case 'MailOutlined':
      return <MailOutlined style={iconStyle} />;
    default:
      return <ApiOutlined style={iconStyle} />;
  }
};

export const NodeConfigPanel: React.FC<NodeConfigPanelProps> = ({
  node,
  components,
  onSave,
  onDelete,
}) => {
  const [form] = Form.useForm();
  const [config, setConfig] = useState<any>({});
  const nodeType = node?.data?.type || 'unknown';
  const nodeDef = getNodeTypeDefinition(nodeType);

  useEffect(() => {
    if (node) {
      const initialConfig = node.data?.config || {};
      form.setFieldsValue({
        label: node.data?.label || node.label || '',
        ...initialConfig,
      });
      setConfig(initialConfig);
    }
  }, [node, form]);

  if (!node) {
    return (
      <div className="empty-panel" style={{ padding: 20, textAlign: 'center' }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>🎯</div>
        <p>选择节点进行配置</p>
        <div style={{ marginTop: 20, textAlign: 'left', fontSize: 12, color: '#666' }}>
          <p>操作指南：</p>
          <ul>
            <li>从左侧拖拽节点到画布</li>
            <li>点击节点选中并配置</li>
            <li>拖拽连接点创建连线</li>
            <li>按住 Shift 平移画布</li>
            <li>Ctrl + 滚轮缩放画布</li>
          </ul>
        </div>
      </div>
    );
  }

  if (!nodeDef) {
    return (
      <Alert
        message="未知节点类型"
        description={`节点类型 "${nodeType}" 暂无配置定义`}
        type="warning"
        showIcon
      />
    );
  }

  // 过滤可用组件
  const getAvailableComponents = () => {
    if (!nodeDef.componentFilter) return [];
    return components.filter((comp) => {
      if (nodeDef.componentFilter?.component_type && 
          comp.component_type !== nodeDef.componentFilter.component_type) {
        return false;
      }
      if (nodeDef.componentFilter?.protocol) {
        const config = comp.execution_config || {};
        if (config.protocol !== nodeDef.componentFilter.protocol) {
          return false;
        }
      }
      return true;
    });
  };

  const handleSave = () => {
    form.validateFields().then((values) => {
      onSave(node.id, {
        label: values.label,
        config: values,
      });
    });
  };

  // 渲染表单字段
  const renderField = (field: ConfigField) => {
    const commonProps = {
      placeholder: field.placeholder,
      style: { width: '100%' },
    };

    switch (field.type) {
      case 'string':
        return <Input {...commonProps} />;
      
      case 'number':
        return (
          <InputNumber
            {...commonProps}
            min={field.name === 'temperature' ? 0 : undefined}
            max={field.name === 'temperature' ? 1 : undefined}
            step={field.name === 'temperature' ? 0.1 : 1}
          />
        );
      
      case 'boolean':
        return <Switch defaultChecked={field.defaultValue} />;
      
      case 'textarea':
        return <TextArea {...commonProps} rows={4} />;
      
      case 'code':
        return (
          <TextArea
            {...commonProps}
            rows={10}
            style={{ ...commonProps.style, fontFamily: 'monospace' }}
          />
        );
      
      case 'json':
        return (
          <TextArea
            {...commonProps}
            rows={6}
            style={{ ...commonProps.style, fontFamily: 'monospace' }}
            placeholder={field.placeholder || '{"key": "value"}'}
          />
        );
      
      case 'select':
        return (
          <Select {...commonProps}>
            {field.options?.map((opt) => (
              <Option key={opt.value} value={opt.value}>
                {opt.label}
              </Option>
            ))}
          </Select>
        );
      
      case 'component-select':
        const availableComps = getAvailableComponents();
        return (
          <Select {...commonProps} showSearch>
            {availableComps.map((comp) => (
              <Option key={comp.id} value={comp.id}>
                <Space>
                  <span>{comp.name}</span>
                  <Tag>{comp.code}</Tag>
                </Space>
              </Option>
            ))}
          </Select>
        );
      
      default:
        return <Input {...commonProps} />;
    }
  };

  // 渲染条件分支特殊配置
  const renderConditionConfig = () => {
    const conditions = config.conditions || [
      { id: 'branch1', name: '条件1', condition: '' },
    ];

    return (
      <>
        <Divider>分支配置</Divider>
        {conditions.map((branch: any, index: number) => (
          <Card
            key={branch.id || index}
            size="small"
            title={
              <Space>
                <Tag color={index === 0 ? 'blue' : index === 1 ? 'green' : 'orange'}>
                  分支 {index + 1}
                </Tag>
              </Space>
            }
            extra={
              conditions.length > 1 && (
                <Button
                  type="text"
                  danger
                  size="small"
                  icon={<DeleteOutlined />}
                  onClick={() => {
                    const newConditions = conditions.filter((_: any, i: number) => i !== index);
                    form.setFieldsValue({ conditions: newConditions });
                    setConfig({ ...config, conditions: newConditions });
                  }}
                />
              )
            }
            style={{ marginBottom: 12 }}
          >
            <Form.Item
              name={['conditions', index, 'name']}
              label="分支名称"
              rules={[{ required: true }]}
              initialValue={branch.name}
            >
              <Input placeholder="如：成功分支" />
            </Form.Item>
            <Form.Item
              name={['conditions', index, 'condition']}
              label="条件表达式"
              rules={[{ required: true }]}
              initialValue={branch.condition}
            >
              <TextArea
                rows={2}
                placeholder="如：{{status}} == 'success'"
              />
            </Form.Item>
          </Card>
        ))}
        <Button
          type="dashed"
          block
          icon={<PlusOutlined />}
          onClick={() => {
            const newConditions = [
              ...conditions,
              { id: `branch${conditions.length + 1}`, name: `条件${conditions.length + 1}`, condition: '' },
            ];
            form.setFieldsValue({ conditions: newConditions });
            setConfig({ ...config, conditions: newConditions });
          }}
        >
          添加分支
        </Button>
        <Form.Item
          name="defaultBranch"
          label="默认分支名称"
          style={{ marginTop: 16 }}
        >
          <Input placeholder="当所有条件不满足时" />
        </Form.Item>
      </>
    );
  };

  // 渲染LLM特殊配置
  const renderLLMConfig = () => {
    return (
      <>
        <Form.Item
          name="model"
          label="模型"
          rules={[{ required: true }]}
        >
          <Select>
            <Option value="gpt-4">GPT-4</Option>
            <Option value="gpt-3.5-turbo">GPT-3.5</Option>
            <Option value="claude">Claude</Option>
            <Option value="local">本地模型</Option>
          </Select>
        </Form.Item>
        
        <Form.Item
          name="prompt"
          label="提示词"
          rules={[{ required: true }]}
        >
          <TextArea
            rows={6}
            placeholder="请输入提示词，使用 {{variable}} 引用变量"
          />
        </Form.Item>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="temperature"
              label="Temperature"
              tooltip="控制输出的随机性，范围0-1"
            >
              <InputNumber min={0} max={1} step={0.1} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="maxTokens"
              label="最大Token数"
            >
              <InputNumber min={1} max={8192} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item
          name="systemPrompt"
          label="系统提示词"
          tooltip="定义AI的角色和行为"
        >
          <TextArea
            rows={3}
            placeholder="你是一个专业的助手..."
          />
        </Form.Item>

        <Form.Item
          name="outputFormat"
          label="输出格式"
        >
          <Select>
            <Option value="text">文本</Option>
            <Option value="json">JSON</Option>
          </Select>
        </Form.Item>

        <Divider>或使用已配置的组件</Divider>
        <Form.Item name="componentId" label="选择AI组件">
          <Select allowClear placeholder="选择预设组件">
            {getAvailableComponents().map((comp) => (
              <Option key={comp.id} value={comp.id}>
                {comp.name}
              </Option>
            ))}
          </Select>
        </Form.Item>
      </>
    );
  };

  // 渲染MCP特殊配置
  const renderMCPConfig = () => {
    return (
      <>
        <Form.Item
          name="serverUrl"
          label="MCP服务器地址"
          rules={[{ required: true }]}
        >
          <Input placeholder="http://localhost:3000/sse" />
        </Form.Item>

        <Form.Item
          name="toolName"
          label="工具名称"
          rules={[{ required: true }]}
        >
          <Input placeholder="要调用的MCP工具名" />
        </Form.Item>

        <Form.Item
          name="parameters"
          label="参数"
        >
          <TextArea
            rows={4}
            style={{ fontFamily: 'monospace' }}
            placeholder='{"key": "value"}'
          />
        </Form.Item>

        <Form.Item
          name="timeout"
          label="超时时间(秒)"
        >
          <InputNumber min={1} max={300} style={{ width: '100%' }} />
        </Form.Item>

        <Divider>或使用已配置的组件</Divider>
        <Form.Item name="componentId" label="选择MCP组件">
          <Select allowClear placeholder="选择预设组件">
            {getAvailableComponents().map((comp) => (
              <Option key={comp.id} value={comp.id}>
                {comp.name}
              </Option>
            ))}
          </Select>
        </Form.Item>
      </>
    );
  };

  // 渲染数据库特殊配置
  const renderDatabaseConfig = () => {
    return (
      <>
        <Form.Item
          name="dbType"
          label="数据库类型"
          rules={[{ required: true }]}
        >
          <Select>
            <Option value="postgresql">PostgreSQL</Option>
            <Option value="mysql">MySQL</Option>
            <Option value="mongodb">MongoDB</Option>
            <Option value="redis">Redis</Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="connection"
          label="连接字符串"
          rules={[{ required: true }]}
        >
          <Input placeholder="postgresql://user:pass@host:port/db" />
        </Form.Item>

        <Form.Item
          name="operation"
          label="操作类型"
          rules={[{ required: true }]}
        >
          <Select>
            <Option value="query">查询</Option>
            <Option value="insert">插入</Option>
            <Option value="update">更新</Option>
            <Option value="delete">删除</Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="sql"
          label="SQL/查询语句"
          rules={[{ required: true }]}
        >
          <TextArea
            rows={6}
            style={{ fontFamily: 'monospace' }}
            placeholder="SELECT * FROM users WHERE id = {{userId}}"
          />
        </Form.Item>

        <Divider>或使用已配置的组件</Divider>
        <Form.Item name="componentId" label="选择数据库组件">
          <Select allowClear placeholder="选择预设组件">
            {getAvailableComponents().map((comp) => (
              <Option key={comp.id} value={comp.id}>
                {comp.name}
              </Option>
            ))}
          </Select>
        </Form.Item>
      </>
    );
  };

  // 渲染HTTP特殊配置
  const renderHTTPConfig = () => {
    return (
      <>
        <Form.Item
          name="method"
          label="请求方法"
          rules={[{ required: true }]}
        >
          <Select>
            <Option value="GET">GET</Option>
            <Option value="POST">POST</Option>
            <Option value="PUT">PUT</Option>
            <Option value="DELETE">DELETE</Option>
            <Option value="PATCH">PATCH</Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="url"
          label="请求URL"
          rules={[{ required: true }]}
        >
          <Input placeholder="https://api.example.com/data" />
        </Form.Item>

        <Form.Item
          name="headers"
          label="请求头"
        >
          <TextArea
            rows={3}
            style={{ fontFamily: 'monospace' }}
            placeholder='{"Authorization": "Bearer {{token}}"}'
          />
        </Form.Item>

        <Form.Item
          name="body"
          label="请求体"
        >
          <TextArea
            rows={4}
            style={{ fontFamily: 'monospace' }}
            placeholder='{"key": "value"}'
          />
        </Form.Item>

        <Form.Item
          name="timeout"
          label="超时时间(秒)"
        >
          <InputNumber min={1} max={300} style={{ width: '100%' }} />
        </Form.Item>
      </>
    );
  };

  // 渲染通用字段
  const renderGenericFields = () => {
    return nodeDef.configFields.map((field) => (
      <Form.Item
        key={field.name}
        name={field.name}
        label={field.label}
        rules={field.required ? [{ required: true, message: `请输入${field.label}` }] : []}
        help={field.description}
      >
        {renderField(field)}
      </Form.Item>
    ));
  };

  // 根据节点类型渲染不同的配置
  const renderConfigByType = () => {
    switch (nodeType) {
      case 'condition':
        return renderConditionConfig();
      case 'llm':
        return renderLLMConfig();
      case 'mcp':
        return renderMCPConfig();
      case 'database':
        return renderDatabaseConfig();
      case 'http':
        return renderHTTPConfig();
      default:
        return renderGenericFields();
    }
  };

  return (
    <div className="node-config-panel" style={{ padding: 16 }}>
      <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 12 }}>
        {getIcon(nodeDef.icon, nodeDef.color)}
        <div>
          <div style={{ fontSize: 16, fontWeight: 'bold' }}>{nodeDef.name}</div>
          <div style={{ fontSize: 12, color: '#666' }}>{nodeDef.description}</div>
        </div>
      </div>

      <Divider style={{ margin: '12px 0' }} />

      <Form
        form={form}
        layout="vertical"
        size="small"
      >
        <Form.Item
          name="label"
          label="节点名称"
          rules={[{ required: true, message: '请输入节点名称' }]}
        >
          <Input placeholder="输入节点名称" />
        </Form.Item>

        {renderConfigByType()}

        <Divider style={{ margin: '16px 0' }} />

        <Space direction="vertical" style={{ width: '100%' }}>
          <Button type="primary" block onClick={handleSave}>
            保存配置
          </Button>
          <Button danger block icon={<DeleteOutlined />} onClick={() => onDelete(node.id)}>
            删除节点
          </Button>
        </Space>
      </Form>
    </div>
  );
};

export default NodeConfigPanel;
