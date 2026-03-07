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
  Tabs,
  message,
} from 'antd';
import {
  DeleteOutlined,
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
import { get } from '../../../../utils/request';

const { TextArea } = Input;
const { Option } = Select;
const { TabPane } = Tabs;

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

// API协议特定的字段
const protocolFieldMap: Record<string, string[]> = {
  http: ['method', 'url', 'headers', 'body', 'timeout'],
  https: ['method', 'url', 'headers', 'body', 'timeout'],
  grpc: ['target', 'service', 'method', 'protoFile', 'timeout'],
  graphql: ['endpoint', 'query', 'variables', 'timeout'],
  soap: ['soapUrl', 'soapAction', 'soapBody', 'timeout'],
  websocket: ['wsUrl', 'wsMessage', 'timeout'],
};

export const NodeConfigPanel: React.FC<NodeConfigPanelProps> = ({
  node,
  components,
  onSave,
  onDelete,
}) => {
  const [form] = Form.useForm();
  const [config, setConfig] = useState<any>({});
  const [selectedProtocol, setSelectedProtocol] = useState<string>('http');
  const [selectedComponentId, setSelectedComponentId] = useState<string | undefined>();
  const [selectedComponent, setSelectedComponent] = useState<Component | null>(null);
  const [lockedFields, setLockedFields] = useState<Set<string>>(new Set());
  const [hiddenFields, setHiddenFields] = useState<Set<string>>(new Set());
  const [apiComponents, setApiComponents] = useState<Component[]>([]);
  
  const nodeType = node?.data?.type || 'unknown';
  const nodeDef = getNodeTypeDefinition(nodeType);

  // 过滤API类型的组件
  useEffect(() => {
    const apiComps = components.filter(c => c.component_type === 'api');
    setApiComponents(apiComps);
  }, [components]);

  useEffect(() => {
    if (node) {
      console.log('[NodeConfigPanel] Loading node data:', { id: node.id, data: node.data });
      
      // 支持两种配置格式：平铺格式（data.xxx）和嵌套格式（data.config.xxx）
      // 优先使用平铺格式
      const nodeData = node.data || {};
      const nestedConfig = nodeData.config || {};
      
      // 合并配置：优先使用平铺的（nodeData），如果平铺的不存在则使用嵌套的（nestedConfig）
      const initialConfig = {
        ...nestedConfig,  // 先展开嵌套配置作为默认值
        ...nodeData,      // 再展开平铺配置（会覆盖嵌套配置中的同名属性）
      };
      
      console.log('[NodeConfigPanel] Initial config:', initialConfig);
      
      // 重置表单并设置新值
      form.resetFields();
      form.setFieldsValue({
        label: nodeData.label || node.label || '',
        ...initialConfig,
      });
      setConfig(initialConfig);
      setSelectedProtocol(initialConfig.protocol || 'http');
      setSelectedComponentId(initialConfig.componentId);
      
      // 恢复组件锁定和隐藏状态
      if (initialConfig.componentId) {
        const comp = apiComponents.find(c => c.id === initialConfig.componentId);
        if (comp && comp.execution_config) {
          setSelectedComponent(comp);
          // 锁定组件配置中的字段
          const execFields = Object.keys(comp.execution_config);
          setLockedFields(new Set(['protocol', ...execFields]));
          // 隐藏组件中已配置的字段（有值的字段）
          const fieldsWithValue = Object.entries(comp.execution_config)
            .filter(([key, value]) => value !== undefined && value !== null && value !== '')
            .map(([key]) => key);
          setHiddenFields(new Set(fieldsWithValue));
        }
      } else {
        setSelectedComponent(null);
        setLockedFields(new Set());
        setHiddenFields(new Set());
      }
    }
  }, [node?.id, node?.data, form, apiComponents]);

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

  const handleSave = () => {
    form.validateFields().then((values) => {
      // 保存时同时保存到 data 和 config（向后兼容）
      onSave(node.id, {
        label: values.label,
        ...values,  // 平铺保存所有配置项
        config: values,  // 同时保留 config 对象（向后兼容）
      });
    });
  };

  // 处理协议切换
  const handleProtocolChange = (protocol: string) => {
    setSelectedProtocol(protocol);
    form.setFieldsValue({ protocol });
  };

  // 处理组件选择
  const handleComponentSelect = (componentId: string) => {
    const selectedComp = apiComponents.find(c => c.id === componentId);
    
    if (!selectedComp) return;
    
    setSelectedComponentId(componentId);
    setSelectedComponent(selectedComp);
    
    if (selectedComp.execution_config) {
      const execConfig = selectedComp.execution_config;
      
      // 锁定组件配置中的字段
      const execFields = Object.keys(execConfig);
      setLockedFields(new Set(['protocol', ...execFields]));
      
      // 隐藏组件中已配置的字段（有非空值的字段）
      const fieldsWithValue = Object.entries(execConfig)
        .filter(([key, value]) => value !== undefined && value !== null && value !== '')
        .map(([key]) => key);
      setHiddenFields(new Set(fieldsWithValue));
      
      // 自动填充组件配置
      const newValues = {
        componentId,
        protocol: execConfig.protocol || 'http',
        ...execConfig,
      };
      form.setFieldsValue(newValues);
      setSelectedProtocol(execConfig.protocol || 'http');
      
      const hiddenFieldNames = fieldsWithValue.filter(f => f !== 'protocol').join(', ');
      if (hiddenFieldNames) {
        message.success(`已加载组件「${selectedComp.name}」，${fieldsWithValue.length}个参数已预设`);
      } else {
        message.success(`已加载组件「${selectedComp.name}」`);
      }
    }
  };

  // 清除组件选择
  const handleClearComponent = () => {
    setSelectedComponentId(undefined);
    setSelectedComponent(null);
    setLockedFields(new Set());
    setHiddenFields(new Set());
    form.setFieldsValue({ componentId: undefined });
    message.info('已清除组件选择，可以自定义配置');
  };

  // 检查字段是否被锁定
  const isFieldLocked = (fieldName: string): boolean => {
    return lockedFields.has(fieldName);
  };

  // 检查字段是否被隐藏（组件中已配置）
  const isFieldHidden = (fieldName: string): boolean => {
    return hiddenFields.has(fieldName);
  };

  // 渲染表单字段
  const renderField = (field: ConfigField, disabled: boolean = false) => {
    // 对于API节点，根据协议过滤字段
    if (nodeType === 'api') {
      const protocolFields = protocolFieldMap[selectedProtocol] || [];
      
      // 通用字段始终显示
      const commonFields = ['protocol', 'componentId', 'timeout'];
      
      // 如果字段不是通用字段，也不在协议特定字段列表中，则不显示
      if (!commonFields.includes(field.name) && !protocolFields.includes(field.name)) {
        return null;
      }
    }

    const isLocked = disabled || isFieldLocked(field.name);
    const commonProps = {
      placeholder: field.placeholder,
      style: { width: '100%' },
      disabled: isLocked,
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
        return <Switch defaultChecked={field.defaultValue} disabled={isLocked} />;
      
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
        // 协议选择特殊处理
        if (field.name === 'protocol') {
          return (
            <Select {...commonProps} onChange={handleProtocolChange}>
              {field.options?.map((opt) => (
                <Option key={opt.value} value={opt.value}>
                  {opt.label}
                </Option>
              ))}
            </Select>
          );
        }
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
        return (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Select 
              {...commonProps} 
              showSearch
              value={selectedComponentId}
              onChange={handleComponentSelect}
              placeholder="选择已注册的API组件（可选）"
              allowClear
              onClear={handleClearComponent}
            >
              {apiComponents.map((comp) => (
                <Option key={comp.id} value={comp.id}>
                  <Space>
                    <span>{comp.name}</span>
                    <Tag color="blue" style={{ fontSize: 12 }}>{comp.execution_config?.protocol || 'http'}</Tag>
                    <span style={{ color: '#999', fontSize: 12 }}>{comp.code}</span>
                  </Space>
                </Option>
              ))}
            </Select>
            {selectedComponentId && (
              <Button type="link" size="small" onClick={handleClearComponent} style={{ padding: 0 }}>
                清除选择，使用自定义配置
              </Button>
            )}
          </Space>
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

  // 根据节点类型渲染不同的配置
  const renderConfigByType = () => {
    switch (nodeType) {
      case 'condition':
        return renderConditionConfig();
      case 'api':
        // 获取当前协议的所有字段
        const protocolFields = protocolFieldMap[selectedProtocol] || [];
        
        return (
          <>
            <Divider orientation="left">基础配置</Divider>
            
            {/* 组件选择 - 始终放在第一个 */}
            <Form.Item
              name="componentId"
              label="选择已注册组件"
              help="选择已注册的API组件可自动填充配置参数"
            >
              <Space direction="vertical" style={{ width: '100%' }}>
                <Select 
                  showSearch
                  value={selectedComponentId}
                  onChange={handleComponentSelect}
                  placeholder="请选择（可选）"
                  allowClear
                  onClear={handleClearComponent}
                  style={{ width: '100%' }}
                >
                  {apiComponents.map((comp) => (
                    <Option key={comp.id} value={comp.id}>
                      <Space>
                        <span>{comp.name}</span>
                        <Tag color="blue" style={{ fontSize: 12 }}>{comp.execution_config?.protocol || 'http'}</Tag>
                        <span style={{ color: '#999', fontSize: 12 }}>{comp.code}</span>
                      </Space>
                    </Option>
                  ))}
                </Select>
                {selectedComponentId && (
                  <Button type="link" size="small" onClick={handleClearComponent} style={{ padding: 0 }}>
                    清除选择，使用自定义配置
                  </Button>
                )}
              </Space>
            </Form.Item>
            
            {/* 协议选择 */}
            {!selectedComponentId && (
              <Form.Item
                name="protocol"
                label="协议类型"
                rules={[{ required: true }]}
              >
                <Select onChange={handleProtocolChange}>
                  <Option value="http">HTTP</Option>
                  <Option value="https">HTTPS</Option>
                  <Option value="grpc">gRPC</Option>
                  <Option value="graphql">GraphQL</Option>
                  <Option value="soap">SOAP</Option>
                  <Option value="websocket">WebSocket</Option>
                </Select>
              </Form.Item>
            )}
            
            {/* 已选择组件时的提示 */}
            {selectedComponentId && (
              <Alert
                message={`已继承组件「${selectedComponent?.name}」的配置`}
                description={
                  hiddenFields.size > 0 
                    ? `其中 ${hiddenFields.size} 个参数已预设，下方仅显示需要补充的配置项`
                    : '组件配置已加载'
                }
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
                action={
                  <Button size="small" type="link" onClick={handleClearComponent}>
                    清除继承
                  </Button>
                }
              />
            )}
            
            {/* 协议配置 - 过滤掉已隐藏的字段 */}
            {nodeDef.configFields
              .filter(field => {
                const commonFields = ['protocol', 'componentId', 'timeout'];
                // 只显示当前协议的字段 + timeout
                const shouldShow = protocolFields.includes(field.name) || field.name === 'timeout';
                // 但隐藏组件中已配置的字段
                const isHidden = isFieldHidden(field.name);
                return shouldShow && !isHidden && !commonFields.includes(field.name);
              })
              .map((field) => (
                <Form.Item
                  key={field.name}
                  name={field.name}
                  label={field.label}
                  rules={field.required ? [{ required: true, message: `请输入${field.label}` }] : []}
                  help={field.description}
                >
                  {renderField(field)}
                </Form.Item>
              ))}
            
            {/* 始终显示 timeout（如果未被隐藏） */}
            {!isFieldHidden('timeout') && (
              <Form.Item
                name="timeout"
                label="超时时间(秒)"
              >
                <InputNumber min={1} max={300} style={{ width: '100%' }} placeholder="30" />
              </Form.Item>
            )}
          </>
        );
      default:
        return nodeDef.configFields.map((field) => {
          const element = renderField(field);
          if (!element) return null;
          return (
            <Form.Item
              key={field.name}
              name={field.name}
              label={field.label}
              rules={field.required ? [{ required: true, message: `请输入${field.label}` }] : []}
              help={field.description}
            >
              {element}
            </Form.Item>
          );
        });
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
