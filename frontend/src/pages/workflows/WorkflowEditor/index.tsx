import { useState, useRef, useEffect } from 'react'
// @ts-ignore
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Button,
  Space,
  Input,
  Form,
  Tabs,
  message,
  Collapse,
  Badge,
  Tooltip,
  Table,
  Tag,
} from 'antd'
import {
  SaveOutlined,
  PlayCircleOutlined,
  RollbackOutlined,
  PlayCircleFilled,
  PauseCircleFilled,
  ApiOutlined,
  RobotOutlined,
  CloudOutlined,
  DatabaseOutlined,
  CodeOutlined,
  BranchesOutlined,
  ClockCircleOutlined,
  NodeIndexOutlined,
  FunctionOutlined,
  MailOutlined,
  FileTextOutlined,
  GlobalOutlined,
  HistoryOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined as ClockIcon,
} from '@ant-design/icons'
import WorkflowCanvas, { WorkflowCanvasRef } from './components/WorkflowCanvas'
import NodeConfigPanel from './components/NodeConfigPanel'
import { getAllNodeTypes, NodeTypeDefinition, NodeCategory } from './types/nodeTypes'
import { Component } from '../../../types/component'
import { get, post, put } from '../../../utils/request'
import './index.less'

const { TabPane } = Tabs
const { Panel } = Collapse

// 图标映射
const iconMap: Record<string, React.ReactNode> = {
  PlayCircleFilled: <PlayCircleFilled />,
  PauseCircleFilled: <PauseCircleFilled />,
  BranchesOutlined: <BranchesOutlined />,
  ClockCircleOutlined: <ClockCircleOutlined />,
  ApiOutlined: <ApiOutlined />,
  DatabaseOutlined: <DatabaseOutlined />,
  CodeOutlined: <CodeOutlined />,
  FunctionOutlined: <FunctionOutlined />,
  RobotOutlined: <RobotOutlined />,
  CloudOutlined: <CloudOutlined />,
  MailOutlined: <MailOutlined />,
  NodeIndexOutlined: <NodeIndexOutlined />,
  FileTextOutlined: <FileTextOutlined />,
  GlobalOutlined: <GlobalOutlined />,
}

// 分类名称映射
const categoryNames: Record<NodeCategory, string> = {
  control: '控制流',
  api: 'API组件',
  database: '数据库',
  message: '消息通知',
  ai: 'AI能力',
  mcp: 'MCP工具',
}

// 分类颜色
const categoryColors: Record<NodeCategory, string> = {
  control: '#1890ff',
  api: '#1890ff',
  database: '#52c41a',
  message: '#fa8c16',
  ai: '#722ed1',
  mcp: '#13c2c2',
}

interface DraggableNodeProps {
  type: string
  name: string
  icon: React.ReactNode
  color: string
  description?: string
}

const DraggableNode: React.FC<DraggableNodeProps> = ({ type, name, icon, color, description }) => {
  const handleDragStart = (e: React.DragEvent) => {
    e.dataTransfer.setData('nodeType', type)
    e.dataTransfer.setData('nodeLabel', name)
    e.dataTransfer.effectAllowed = 'copy'
  }

  return (
    <Tooltip title={description} placement="right">
      <div
        className="draggable-node"
        draggable
        onDragStart={handleDragStart}
        style={{ borderLeftColor: color }}
      >
        <span className="node-icon" style={{ color }}>
          {icon}
        </span>
        <span className="node-name">{name}</span>
      </div>
    </Tooltip>
  )
}

export const WorkflowEditorPage = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEditing = !!id
  const [form] = Form.useForm()
  const [activeTab, setActiveTab] = useState('design')
  const [selectedNode, setSelectedNode] = useState<any>(null)
  const [workflowName, setWorkflowName] = useState('')
  const [components, setComponents] = useState<Component[]>([])
  const [, setLoading] = useState(false)
  const [executions, setExecutions] = useState<any[]>([])
  const [executionsLoading, setExecutionsLoading] = useState(false)
  const canvasRef = useRef<WorkflowCanvasRef>(null)

  // 使用 Form.useWatch 监听 name 字段变化
  const watchedName = Form.useWatch('name', form)

  // 加载组件列表
  useEffect(() => {
    const loadComponents = async () => {
      try {
        const res = await get('/components')
        if (res.data) {
          setComponents(res.data)
        }
      } catch (error) {
        console.error('加载组件失败:', error)
      }
    }
    loadComponents()
  }, [])

  // 加载工作流数据
  useEffect(() => {
    if (isEditing && id) {
      const loadWorkflow = async () => {
        try {
          setLoading(true)
          const res = await get(`/workflows/${id}`)
          console.log('[loadWorkflow] Loaded workflow:', res)
          if (res) {
            setWorkflowName(res.name || '')
            // 使用 setTimeout 确保表单已经挂载
            setTimeout(() => {
              form.setFieldsValue({
                name: res.name,
                description: res.description,
                category: res.category_id,
              })
            }, 0)
            // 加载画布数据
            if (res.definition && canvasRef.current) {
              console.log('[loadWorkflow] Definition nodes:', res.definition.nodes?.map((n: any) => ({
                id: n.id,
                type: n.type,
                url: n.data?.url,
                protocol: n.data?.protocol
              })))
              canvasRef.current.loadGraphData(res.definition)
            }
          }
        } catch (error) {
          message.error('加载工作流失败')
        } finally {
          setLoading(false)
        }
      }
      loadWorkflow()
    }
  }, [id, isEditing, form])

  // 加载执行记录
  const loadExecutions = async () => {
    if (!id) return
    
    try {
      setExecutionsLoading(true)
      const res = await get(`/workflows/${id}/executions`, { params: { page: 1, page_size: 10 } })
      if (res && res.data) {
        setExecutions(res.data)
      }
    } catch (error) {
      console.error('加载执行记录失败:', error)
    } finally {
      setExecutionsLoading(false)
    }
  }

  // 当切换到执行记录标签时加载数据
  useEffect(() => {
    if (activeTab === 'executions' && id) {
      loadExecutions()
    }
  }, [activeTab, id])

  const handleSave = async () => {
    try {
      // 获取表单值（不强制验证）
      const values = form.getFieldsValue()
      const graphData = canvasRef.current?.getGraphData()
      
      console.log('[handleSave] Form values:', values)
      console.log('[handleSave] Graph data:', graphData)
      
      // 如果没有名称，使用默认值
      const name = values.name || workflowName || '未命名工作流'
      
      // 检查节点数据 - 特别关注 API 节点的 URL
      const nodesWithConfig = graphData?.nodes?.map((n: any) => ({
        id: n.id,
        type: n.type,
        url: n.data?.url,
        protocol: n.data?.protocol,
        method: n.data?.method,
        data: n.data
      }))
      console.log('[handleSave] Nodes with config:', nodesWithConfig)
      
      const workflowData = {
        name,
        description: values.description || '',
        definition: graphData || { nodes: [], edges: [] },
        variables: [],
        triggers: [],
        tags: [],
      }

      if (isEditing && id) {
        await put(`/workflows/${id}`, workflowData)
        message.success('工作流更新成功')
      } else {
        const result: any = await post('/workflows', workflowData)
        message.success('工作流创建成功')
        // 跳转到编辑页面
        if (result && result.id) {
          navigate(`/workflows/${result.id}`)
        } else {
          navigate('/workflows')
        }
      }
    } catch (error: any) {
      console.error('保存失败:', error)
      message.error(error.response?.data?.detail || '保存失败')
    }
  }

  const handlePublish = async () => {
    if (!id) {
      message.warning('请先保存工作流')
      return
    }
    
    try {
      await post(`/workflows/${id}/publish`, {})
      message.success('工作流发布成功')
    } catch (error: any) {
      console.error('发布失败:', error)
      message.error(error.response?.data?.detail || '发布失败')
    }
  }

  const handleExecute = async () => {
    // 如果没有id，先保存工作流
    if (!id) {
      message.info('正在保存工作流...')
      await handleSave()
      return
    }
    
    try {
      message.loading({ content: '正在执行工作流...', key: 'execute', duration: 0 })
      const result: any = await post(`/workflows/${id}/execute`, { input_data: {} })
      message.success({ content: '工作流执行完成', key: 'execute' })
      
      // 跳转到执行详情页
      if (result?.id) {
        navigate(`/workflows/${id}/executions/${result.id}`)
      }
    } catch (error: any) {
      message.error({ content: error.response?.data?.detail || '执行失败', key: 'execute' })
      console.error('执行失败:', error)
    }
  }

  const handleBack = () => {
    navigate('/workflows')
  }

  // 查看执行详情
  const handleViewExecution = (executionId: string) => {
    navigate(`/workflows/${id}/executions/${executionId}`)
  }

  // 查看所有执行记录
  const handleViewAllExecutions = () => {
    navigate(`/workflows/${id}/executions`)
  }

  // 获取状态标签
  const getExecutionStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; icon: React.ReactNode; text: string }> = {
      pending: { color: 'default', icon: <ClockIcon />, text: '待执行' },
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

  const handleAddStartNode = () => {
    if (canvasRef.current) {
      canvasRef.current.addNode('start', 100, 50)
      message.success('已添加开始节点')
    }
  }

  const handleAddEndNode = () => {
    if (canvasRef.current) {
      canvasRef.current.addNode('end', 100, 400)
      message.success('已添加结束节点')
    }
  }

  const handleClearCanvas = () => {
    if (canvasRef.current) {
      canvasRef.current.loadGraphData({ cells: [] })
      setSelectedNode(null)
      message.success('画布已清空')
    }
  }

  const handleNodeSave = (nodeId: string, config: any) => {
    const graph = canvasRef.current?.getGraph()
    if (!graph) return

    const cell = graph.getCellById(nodeId)
    if (cell && cell.isNode()) {
      const node = cell as any
      
      // config 结构：{ label, ...values, config: values }
      const { config: nestedConfig, label, ...configValues } = config
      
      // 构建新的 data 对象 - 完全替换旧数据
      const newData = {
        type: node.data?.type || node.shape?.replace('-node', ''),
        label: label || node.data?.label || node.attr('label/text'),
        ...configValues,  // 所有配置值平铺
        // 同时保存嵌套 config 以保持兼容性
        config: { ...configValues },
      }
      
      // 深拷贝确保数据正确保存
      const dataToSave = JSON.parse(JSON.stringify(newData))
      
      // 使用 setData 保存，完全替换旧数据
      node.setData(dataToSave)
      
      // 更新节点标签
      if (label) {
        node.attr('label/text', label)
      }
      
      console.log('[handleNodeSave] Saved node data:', { nodeId, data: dataToSave })
      message.success('节点配置已保存')
    }
  }

  const handleNodeDelete = (nodeId: string) => {
    const graph = canvasRef.current?.getGraph()
    if (!graph) return

    const node = graph.getCellById(nodeId)
    if (node) {
      graph.removeCell(node)
      setSelectedNode(null)
      message.success('节点已删除')
    }
  }

  // 按分类分组节点类型
  const nodeTypesByCategory = getAllNodeTypes().reduce((acc, nodeType) => {
    if (!acc[nodeType.category]) {
      acc[nodeType.category] = []
    }
    acc[nodeType.category].push(nodeType)
    return acc
  }, {} as Record<NodeCategory, NodeTypeDefinition[]>)

  // 分类排序
  const categoryOrder: NodeCategory[] = ['control', 'api', 'database', 'ai', 'mcp', 'message']

  return (
    <div className="workflow-editor-page">
      <Card
        title={
          <Space>
            <span>{isEditing ? '编辑工作流' : '新建工作流'}</span>
            {watchedName && <span style={{ color: '#999', fontSize: 14 }}>- {watchedName}</span>}
          </Space>
        }
        extra={
          <Space>
            <Button icon={<RollbackOutlined />} onClick={handleBack}>
              返回
            </Button>
            <Button icon={<PlayCircleOutlined />} onClick={handleExecute}>
              测试执行
            </Button>
            <Button type="primary" icon={<SaveOutlined />} onClick={handleSave}>
              保存
            </Button>
            <Button type="primary" ghost onClick={handlePublish}>
              发布
            </Button>
          </Space>
        }
      >
        {/* 顶部基本信息区域 */}
        <div className="workflow-basic-info" style={{ marginBottom: 16, paddingBottom: 16, borderBottom: '1px solid #f0f0f0' }}>
          <Form form={form} layout="inline" style={{ flexWrap: 'nowrap' }}>
            <Form.Item
              name="name"
              label="工作流名称"
              rules={[{ required: true, message: '请输入工作流名称' }]}
              style={{ flex: 1, marginRight: 16 }}
            >
              <Input
                placeholder="输入工作流名称"
                onChange={(e) => setWorkflowName(e.target.value)}
              />
            </Form.Item>
            <Form.Item
              name="description"
              label="工作流描述"
              style={{ flex: 2 }}
            >
              <Input.TextArea
                rows={1}
                placeholder="描述工作流的功能和用途（可选）"
                style={{ minHeight: 32, resize: 'none' }}
              />
            </Form.Item>
          </Form>
        </div>

        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="设计" key="design">
            <div className="workflow-designer">
              {/* 左侧组件面板 */}
              <div className="component-panel">
                <div className="panel-title">
                  组件库
                  <div className="panel-actions">
                    <Button size="small" type="link" onClick={handleAddStartNode}>
                      +开始
                    </Button>
                    <Button size="small" type="link" onClick={handleAddEndNode}>
                      +结束
                    </Button>
                    <Button size="small" type="link" danger onClick={handleClearCanvas}>
                      清空
                    </Button>
                  </div>
                </div>

                <Collapse defaultActiveKey={['control', 'api']} ghost>
                  {categoryOrder.map((category) => {
                    const nodeTypes = nodeTypesByCategory[category]
                    if (!nodeTypes || nodeTypes.length === 0) return null

                    return (
                      <Panel
                        header={
                          <Space>
                            <Badge color={categoryColors[category]} />
                            <span>{categoryNames[category]}</span>
                          </Space>
                        }
                        key={category}
                      >
                        <div className="node-list">
                          {nodeTypes.map((nodeType) => (
                            <DraggableNode
                              key={nodeType.type}
                              type={nodeType.type}
                              name={nodeType.name}
                              icon={iconMap[nodeType.icon] || <ApiOutlined />}
                              color={nodeType.color}
                              description={nodeType.description}
                            />
                          ))}
                        </div>
                      </Panel>
                    )
                  })}
                </Collapse>

                <div className="panel-tips">
                  <p>💡 提示：</p>
                  <p>1. 拖拽左侧组件到画布</p>
                  <p>2. 连接节点端口创建流程</p>
                  <p>3. 双击节点编辑名称</p>
                  <p>4. 按 Delete 删除选中节点</p>
                </div>
              </div>

              {/* 中间画布区域 */}
              <div className="canvas-area">
                <WorkflowCanvas
                  ref={canvasRef}
                  onNodeSelect={setSelectedNode}
                  onGraphChange={(data) => console.log('画布变化:', data)}
                />

                {/* 画布工具栏 */}
                <div className="canvas-toolbar">
                  <Button size="small" onClick={handleAddStartNode} type="primary" ghost>
                    + 开始节点
                  </Button>
                  <Button size="small" onClick={handleAddEndNode} type="primary" ghost danger>
                    + 结束节点
                  </Button>
                  <Button size="small" onClick={handleClearCanvas} danger>
                    清空画布
                  </Button>
                </div>
              </div>

              {/* 右侧属性面板 */}
              <div className="property-panel">
                <div className="panel-title">
                  {selectedNode ? '节点配置' : '属性面板'}
                </div>
                <div className="property-content">
                  {selectedNode ? (
                    <NodeConfigPanel
                      node={selectedNode}
                      components={components}
                      onSave={handleNodeSave}
                      onDelete={handleNodeDelete}
                    />
                  ) : (
                    <div className="empty-panel">
                      <div className="empty-icon">🎯</div>
                      <p>选择节点进行配置</p>
                      <div className="tips">
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
                  )}
                </div>
              </div>
            </div>
          </TabPane>

          <TabPane tab="配置" key="config">
            <Form form={form} layout="vertical" style={{ maxWidth: 800 }}>
              <Form.Item name="category" label="分类">
                <Input placeholder="选择分类" />
              </Form.Item>
              <Form.Item name="tags" label="标签">
                <Input placeholder="输入标签，用逗号分隔" />
              </Form.Item>
            </Form>
          </TabPane>

          <TabPane tab="变量" key="variables">
            <div className="empty-tab">
              <h3>工作流变量</h3>
              <p>定义工作流的输入输出变量</p>
              <p style={{ color: '#999', marginTop: 20 }}>
                功能开发中...
              </p>
            </div>
          </TabPane>

          <TabPane tab="执行记录" key="executions">
            <div style={{ padding: 16 }}>
              <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
                <h3 style={{ margin: 0 }}>执行历史</h3>
                <Button type="link" icon={<HistoryOutlined />} onClick={handleViewAllExecutions}>
                  查看全部
                </Button>
              </div>
              <Table
                dataSource={executions}
                rowKey="id"
                loading={executionsLoading}
                pagination={false}
                size="small"
                columns={[
                  {
                    title: '执行ID',
                    dataIndex: 'id',
                    key: 'id',
                    render: (id: string) => <span style={{ fontFamily: 'monospace', fontSize: 12 }}>{id.substring(0, 8)}...</span>,
                  },
                  {
                    title: '状态',
                    dataIndex: 'status',
                    key: 'status',
                    render: (status: string) => getExecutionStatusTag(status),
                  },
                  {
                    title: '耗时',
                    dataIndex: 'duration_ms',
                    key: 'duration_ms',
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
                    render: (date: string) => new Date(date).toLocaleString('zh-CN'),
                  },
                  {
                    title: '操作',
                    key: 'action',
                    render: (_: any, record: any) => (
                      <Button
                        type="link"
                        size="small"
                        icon={<EyeOutlined />}
                        onClick={() => handleViewExecution(record.id)}
                      >
                        详情
                      </Button>
                    ),
                  },
                ]}
              />
            </div>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default WorkflowEditorPage
