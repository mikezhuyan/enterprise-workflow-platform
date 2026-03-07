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
  const canvasRef = useRef<WorkflowCanvasRef>(null)

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
          if (res) {
            setWorkflowName(res.name || '')
            form.setFieldsValue({
              name: res.name,
              description: res.description,
              category: res.category_id,
            })
            // 加载画布数据
            if (res.definition && canvasRef.current) {
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

  const handleSave = async () => {
    try {
      // 获取表单值（不强制验证）
      const values = form.getFieldsValue()
      const graphData = canvasRef.current?.getGraphData()
      
      // 如果没有名称，使用默认值
      const name = values.name || workflowName || '未命名工作流'
      
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

  const handlePublish = () => {
    message.success('工作流发布成功')
  }

  const handleExecute = async () => {
    // 如果没有id，先保存工作流
    if (!id) {
      message.info('正在保存工作流...')
      await handleSave()
      return
    }
    
    try {
      await post(`/workflows/${id}/execute`, { input_data: {} })
      message.success('开始执行工作流')
    } catch (error: any) {
      console.error('执行失败:', error)
      message.error(error.response?.data?.detail || '执行失败')
    }
  }

  const handleBack = () => {
    navigate('/workflows')
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
      const data = node.getData() || {}
      node.setData({ ...data, ...config })
      if (config.label) {
        node.attr('label/text', config.label)
      }
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
            {workflowName && <span style={{ color: '#999', fontSize: 14 }}>- {workflowName}</span>}
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
              <Form.Item
                name="name"
                label="工作流名称"
                rules={[{ required: true, message: '请输入工作流名称' }]}
              >
                <Input
                  placeholder="输入工作流名称"
                  value={workflowName}
                  onChange={(e) => setWorkflowName(e.target.value)}
                />
              </Form.Item>
              <Form.Item name="description" label="工作流描述">
                <Input.TextArea rows={4} placeholder="描述工作流的功能和用途" />
              </Form.Item>
              <Form.Item name="category" label="分类">
                <Input placeholder="选择分类" />
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
            <div className="empty-tab">
              <h3>执行历史</h3>
              <p>查看工作流执行历史</p>
              <p style={{ color: '#999', marginTop: 20 }}>
                功能开发中...
              </p>
            </div>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default WorkflowEditorPage
