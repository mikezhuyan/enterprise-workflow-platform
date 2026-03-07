import { useEffect, useRef, forwardRef, useImperativeHandle } from 'react'
import { Graph, Node } from '@antv/x6'
import { Selection } from '@antv/x6-plugin-selection'
import { Snapline } from '@antv/x6-plugin-snapline'
import { Keyboard } from '@antv/x6-plugin-keyboard'
import { message } from 'antd'
import { getNodeTypeDefinition } from '../types/nodeTypes'

interface WorkflowCanvasProps {
  onNodeSelect?: (node: Node | null) => void
  onGraphChange?: (data: any) => void
}

export interface WorkflowCanvasRef {
  addNode: (type: string, x: number, y: number, data?: any) => Node | null
  getGraphData: () => any
  loadGraphData: (data: any) => void
  getGraph: () => Graph | null
}

// 注册所有节点类型
const registerNodes = () => {
  // 开始节点
  Graph.registerNode(
    'start-node',
    {
      inherit: 'circle',
      width: 60,
      height: 60,
      attrs: {
        body: {
          stroke: '#52c41a',
          fill: '#f6ffed',
          strokeWidth: 2,
        },
        label: {
          text: '开始',
          fill: '#52c41a',
          fontSize: 14,
          fontWeight: 'bold',
        },
      },
      ports: {
        groups: {
          out: {
            position: 'bottom',
            attrs: {
              circle: {
                r: 5,
                magnet: true,
                stroke: '#52c41a',
                fill: '#fff',
                strokeWidth: 2,
              },
            },
          },
        },
        items: [{ id: 'out', group: 'out' }],
      },
    },
    true
  )

  // 结束节点
  Graph.registerNode(
    'end-node',
    {
      inherit: 'circle',
      width: 60,
      height: 60,
      attrs: {
        body: {
          stroke: '#ff4d4f',
          fill: '#fff2f0',
          strokeWidth: 2,
        },
        label: {
          text: '结束',
          fill: '#ff4d4f',
          fontSize: 14,
          fontWeight: 'bold',
        },
      },
      ports: {
        groups: {
          in: {
            position: 'top',
            attrs: {
              circle: {
                r: 5,
                magnet: true,
                stroke: '#ff4d4f',
                fill: '#fff',
                strokeWidth: 2,
              },
            },
          },
        },
        items: [{ id: 'in', group: 'in' }],
      },
    },
    true
  )

  // 条件节点（菱形）- 支持多输出
  Graph.registerNode(
    'condition-node',
    {
      inherit: 'polygon',
      width: 100,
      height: 80,
      attrs: {
        body: {
          refPoints: '50,0 100,50 50,100 0,50',
          stroke: '#fa8c16',
          fill: '#fff7e6',
          strokeWidth: 2,
        },
        label: {
          fill: '#fa8c16',
          fontSize: 12,
          fontWeight: 'bold',
        },
      },
      ports: {
        groups: {
          in: {
            position: 'top',
            attrs: {
              circle: {
                r: 5,
                magnet: true,
                stroke: '#fa8c16',
                fill: '#fff',
                strokeWidth: 2,
              },
            },
          },
          out: {
            position: 'bottom',
            attrs: {
              circle: {
                r: 5,
                magnet: true,
                stroke: '#fa8c16',
                fill: '#fff',
                strokeWidth: 2,
              },
            },
          },
        },
        items: [{ id: 'in', group: 'in' }],
      },
    },
    true
  )

  // API节点
  Graph.registerNode(
    'api-node',
    {
      inherit: 'rect',
      width: 180,
      height: 60,
      attrs: {
        body: {
          stroke: '#1890ff',
          fill: '#e6f7ff',
          strokeWidth: 2,
          rx: 6,
          ry: 6,
        },
        label: {
          fill: '#1890ff',
          fontSize: 14,
          fontWeight: 'bold',
        },
      },
      ports: {
        groups: {
          in: {
            position: 'top',
            attrs: {
              circle: {
                r: 5,
                magnet: true,
                stroke: '#1890ff',
                fill: '#fff',
                strokeWidth: 2,
              },
            },
          },
          out: {
            position: 'bottom',
            attrs: {
              circle: {
                r: 5,
                magnet: true,
                stroke: '#1890ff',
                fill: '#fff',
                strokeWidth: 2,
              },
            },
          },
        },
        items: [
          { id: 'in', group: 'in' },
          { id: 'out', group: 'out' },
        ],
      },
    },
    true
  )

  // 数据库节点
  Graph.registerNode(
    'database-node',
    {
      inherit: 'rect',
      width: 180,
      height: 60,
      attrs: {
        body: {
          stroke: '#52c41a',
          fill: '#f6ffed',
          strokeWidth: 2,
          rx: 6,
          ry: 6,
        },
        label: {
          fill: '#52c41a',
          fontSize: 14,
          fontWeight: 'bold',
        },
      },
      ports: {
        groups: {
          in: {
            position: 'top',
            attrs: {
              circle: {
                r: 5,
                magnet: true,
                stroke: '#52c41a',
                fill: '#fff',
                strokeWidth: 2,
              },
            },
          },
          out: {
            position: 'bottom',
            attrs: {
              circle: {
                r: 5,
                magnet: true,
                stroke: '#52c41a',
                fill: '#fff',
                strokeWidth: 2,
              },
            },
          },
        },
        items: [
          { id: 'in', group: 'in' },
          { id: 'out', group: 'out' },
        ],
      },
    },
    true
  )

  // AI节点
  Graph.registerNode(
    'ai-node',
    {
      inherit: 'rect',
      width: 180,
      height: 60,
      attrs: {
        body: {
          stroke: '#722ed1',
          fill: '#f9f0ff',
          strokeWidth: 2,
          rx: 6,
          ry: 6,
        },
        label: {
          fill: '#722ed1',
          fontSize: 14,
          fontWeight: 'bold',
        },
      },
      ports: {
        groups: {
          in: {
            position: 'top',
            attrs: {
              circle: {
                r: 5,
                magnet: true,
                stroke: '#722ed1',
                fill: '#fff',
                strokeWidth: 2,
              },
            },
          },
          out: {
            position: 'bottom',
            attrs: {
              circle: {
                r: 5,
                magnet: true,
                stroke: '#722ed1',
                fill: '#fff',
                strokeWidth: 2,
              },
            },
          },
        },
        items: [
          { id: 'in', group: 'in' },
          { id: 'out', group: 'out' },
        ],
      },
    },
    true
  )

  // MCP节点
  Graph.registerNode(
    'mcp-node',
    {
      inherit: 'rect',
      width: 180,
      height: 60,
      attrs: {
        body: {
          stroke: '#13c2c2',
          fill: '#e6fffb',
          strokeWidth: 2,
          rx: 6,
          ry: 6,
        },
        label: {
          fill: '#13c2c2',
          fontSize: 14,
          fontWeight: 'bold',
        },
      },
      ports: {
        groups: {
          in: {
            position: 'top',
            attrs: {
              circle: {
                r: 5,
                magnet: true,
                stroke: '#13c2c2',
                fill: '#fff',
                strokeWidth: 2,
              },
            },
          },
          out: {
            position: 'bottom',
            attrs: {
              circle: {
                r: 5,
                magnet: true,
                stroke: '#13c2c2',
                fill: '#fff',
                strokeWidth: 2,
              },
            },
          },
        },
        items: [
          { id: 'in', group: 'in' },
          { id: 'out', group: 'out' },
        ],
      },
    },
    true
  )

  // 消息节点
  Graph.registerNode(
    'message-node',
    {
      inherit: 'rect',
      width: 180,
      height: 60,
      attrs: {
        body: {
          stroke: '#fa8c16',
          fill: '#fff7e6',
          strokeWidth: 2,
          rx: 6,
          ry: 6,
        },
        label: {
          fill: '#fa8c16',
          fontSize: 14,
          fontWeight: 'bold',
        },
      },
      ports: {
        groups: {
          in: {
            position: 'top',
            attrs: {
              circle: {
                r: 5,
                magnet: true,
                stroke: '#fa8c16',
                fill: '#fff',
                strokeWidth: 2,
              },
            },
          },
          out: {
            position: 'bottom',
            attrs: {
              circle: {
                r: 5,
                magnet: true,
                stroke: '#fa8c16',
                fill: '#fff',
                strokeWidth: 2,
              },
            },
          },
        },
        items: [
          { id: 'in', group: 'in' },
          { id: 'out', group: 'out' },
        ],
      },
    },
    true
  )

  // 通用组件节点
  Graph.registerNode(
    'component-node',
    {
      inherit: 'rect',
      width: 180,
      height: 60,
      attrs: {
        body: {
          stroke: '#1890ff',
          fill: '#e6f7ff',
          strokeWidth: 2,
          rx: 6,
          ry: 6,
        },
        label: {
          fill: '#1890ff',
          fontSize: 14,
          fontWeight: 'bold',
        },
      },
      ports: {
        groups: {
          in: {
            position: 'top',
            attrs: {
              circle: {
                r: 5,
                magnet: true,
                stroke: '#1890ff',
                fill: '#fff',
                strokeWidth: 2,
              },
            },
          },
          out: {
            position: 'bottom',
            attrs: {
              circle: {
                r: 5,
                magnet: true,
                stroke: '#1890ff',
                fill: '#fff',
                strokeWidth: 2,
              },
            },
          },
        },
        items: [
          { id: 'in', group: 'in' },
          { id: 'out', group: 'out' },
        ],
      },
    },
    true
  )
}

// 根据节点类型获取对应的shape
const getNodeShape = (type: string): string => {
  const shapeMap: Record<string, string> = {
    start: 'start-node',
    end: 'end-node',
    condition: 'condition-node',
    api: 'api-node',
    http: 'api-node',
    https: 'api-node',
    database: 'database-node',
    llm: 'ai-node',
    ai: 'ai-node',
    mcp: 'mcp-node',
    email: 'message-node',
    message: 'message-node',
  }
  return shapeMap[type] || 'component-node'
}

export const WorkflowCanvas = forwardRef<WorkflowCanvasRef, WorkflowCanvasProps>(
  ({ onNodeSelect, onGraphChange }, ref) => {
    const containerRef = useRef<HTMLDivElement>(null)
    const graphRef = useRef<Graph | null>(null)

    useEffect(() => {
      if (!containerRef.current) return

      // 注册节点
      registerNodes()

      // 创建画布
      const graph: Graph = new Graph({
        container: containerRef.current,
        width: containerRef.current.clientWidth,
        height: containerRef.current.clientHeight,
        grid: {
          size: 10,
          visible: true,
          type: 'dot',
          args: {
            color: '#e5e5e5',
          },
        },
        connecting: {
          snap: true,
          allowBlank: false,
          allowLoop: false,
          highlight: true,
          connector: 'rounded',
          connectionPoint: 'boundary',
          router: {
            name: 'manhattan',
            args: {
              padding: 20,
            },
          },
          validateConnection({ sourceMagnet, targetMagnet }) {
            if (sourceMagnet?.getAttribute('port-group') === 'in') {
              return false
            }
            if (targetMagnet?.getAttribute('port-group') === 'out') {
              return false
            }
            return true
          },
          createEdge(): any {
            return this.createEdge({
              attrs: {
                line: {
                  stroke: '#a0a0a0',
                  strokeWidth: 2,
                  targetMarker: {
                    name: 'classic',
                    size: 8,
                  },
                },
              },
              labels: [
                {
                  attrs: {
                    label: {
                      text: '',
                      fill: '#666',
                      fontSize: 12,
                    },
                  },
                },
              ],
            })
          },
        },
        background: {
          color: '#fafafa',
        },
        panning: {
          enabled: true,
          modifiers: 'shift',
        },
        mousewheel: {
          enabled: true,
          modifiers: 'ctrl',
          factor: 1.1,
          maxScale: 2,
          minScale: 0.5,
        },
      })

      // 添加插件
      graph.use(
        new Selection({
          enabled: true,
          multiple: true,
          rubberband: true,
          movable: true,
          showNodeSelectionBox: true,
          showEdgeSelectionBox: true,
        })
      )
      graph.use(new Snapline({ enabled: true }))
      graph.use(
        new Keyboard({
          enabled: true,
          global: false,
        })
      )

      // 键盘快捷键 - 删除选中节点
      graph.bindKey(['delete', 'backspace'], () => {
        const cells = graph.getSelectedCells()
        if (cells.length) {
          graph.removeCells(cells)
          message.success('已删除选中节点')
        }
      })

      // 画布变化监听
      graph.on('node:added', () => {
        onGraphChange?.(graph.toJSON())
      })

      graph.on('node:removed', () => {
        onGraphChange?.(graph.toJSON())
      })

      graph.on('edge:added', () => {
        onGraphChange?.(graph.toJSON())
      })

      graph.on('edge:removed', () => {
        onGraphChange?.(graph.toJSON())
      })

      // 节点选中事件
      graph.on('node:click', ({ node }: { node: Node }) => {
        onNodeSelect?.(node)
        graph.select(node)
      })

      graph.on('blank:click', () => {
        onNodeSelect?.(null)
        graph.cleanSelection()
      })

      // 双击编辑标签
      graph.on('node:dblclick', ({ node }: { node: Node }) => {
        const label = node.attr('label/text') as string
        const newLabel = window.prompt('编辑节点名称:', label)
        if (newLabel !== null && newLabel !== label) {
          node.attr('label/text', newLabel)
          const data = node.getData() || {}
          node.setData({ ...data, label: newLabel })
        }
      })

      graphRef.current = graph

      // 窗口大小调整
      const handleResize = () => {
        if (containerRef.current && graphRef.current) {
          graphRef.current.resize(
            containerRef.current.clientWidth,
            containerRef.current.clientHeight
          )
        }
      }
      window.addEventListener('resize', handleResize)

      return () => {
        window.removeEventListener('resize', handleResize)
        graph.dispose()
        graphRef.current = null
      }
    }, [])

    // 添加节点的公共方法
    const addNode = (type: string, x: number, y: number, data?: any): Node | null => {
      if (!graphRef.current) return null

      const graph = graphRef.current
      const nodeDef = getNodeTypeDefinition(type)
      const shape = getNodeShape(type)
      const color = nodeDef?.color || '#1890ff'
      const label = data?.label || nodeDef?.name || '组件'

      const nodeData = { 
        type, 
        label, 
        color,
        config: data?.config || {},
        ...data 
      }

      let node: Node

      if (type === 'condition') {
        // 条件节点需要动态添加输出端口
        node = graph.addNode({
          shape,
          x,
          y,
          label,
          data: nodeData,
        })
        
        // 添加两个默认分支输出
        node.addPort({
          id: 'out-true',
          group: 'out',
          attrs: { text: { text: '是' } },
        })
        node.addPort({
          id: 'out-false',
          group: 'out',
          attrs: { text: { text: '否' } },
        })
      } else {
        node = graph.addNode({
          shape,
          x,
          y,
          label,
          data: nodeData,
        })
      }

      return node
    }

    // 转换X6数据为WorkflowDefinition格式
    const convertToWorkflowDefinition = (graphData: any) => {
      if (!graphData || !graphData.cells) {
        return { nodes: [], edges: [] }
      }

      const nodes = graphData.cells
        .filter((cell: any) => cell.shape && !cell.shape.includes('edge'))
        .map((cell: any) => {
          // X6 toJSON() 格式：position 是对象 {x, y}，size 是对象 {width, height}
          const x = cell.position?.x ?? 0
          const y = cell.position?.y ?? 0
          const width = cell.size?.width ?? 180
          const height = cell.size?.height ?? 60
          
          // 获取节点数据 - X6 的 data 属性
          const nodeData = cell.data || {}
          
          // 获取标签
          const label = nodeData.label || cell.attrs?.label?.text || cell.attrs?.text?.text || cell.id
          
          // 获取节点类型
          const nodeType = nodeData.type || cell.shape?.replace('-node', '')
          
          // 展开 config 中的配置（向后兼容）
          const nodeConfig = nodeData.config || {}
          
          // 关键修复：对于每个属性，优先使用 nodeData 中的值（新数据），如果不存在则使用 nodeConfig 中的值（旧数据）
          // 这样可以确保更新后的数据不会被旧数据覆盖
          const mergedConfig: any = {}
          
          // 先添加 config 中的所有属性（作为默认值）
          Object.keys(nodeConfig).forEach(key => {
            mergedConfig[key] = nodeConfig[key]
          })
          
          // 然后用 nodeData 中的属性覆盖（新数据优先）
          // 但要排除 'config' 属性本身，避免循环引用
          Object.keys(nodeData).forEach(key => {
            if (key !== 'config') {
              mergedConfig[key] = nodeData[key]
            }
          })
          
          // 构建最终的 data 对象
          const finalData = {
            label,
            type: nodeType,
            ...mergedConfig,
          }
          
          return {
            id: cell.id,
            type: nodeType,
            position: { x, y },
            data: finalData,
            width,
            height,
          }
        })

      const edges = graphData.cells
        .filter((cell: any) => cell.shape === 'edge' || cell.shape?.includes('edge'))
        .map((cell: any) => ({
          id: cell.id,
          source: cell.source?.cell || cell.source,
          target: cell.target?.cell || cell.target,
          source_handle: cell.source?.port,
          target_handle: cell.target?.port,
          label: cell.labels?.[0]?.attrs?.label?.text || cell.label || '',
        }))

      console.log('[WorkflowCanvas] Converted to definition:', { 
        nodeCount: nodes.length, 
        edgeCount: edges.length, 
        nodes: nodes.map((n: any) => ({ 
          id: n.id, 
          type: n.type, 
          hasUrl: !!n.data?.url,
          hasMethod: !!n.data?.method,
          data: n.data 
        })) 
      })
      return { nodes, edges }
    }

    // 转换WorkflowDefinition为X6格式
    const convertFromWorkflowDefinition = (definition: any) => {
      if (!definition || (!definition.nodes && !definition.cells)) {
        return { cells: [] }
      }

      // 如果已经是X6格式，直接返回
      if (definition.cells) {
        return definition
      }

      const nodeCells = (definition.nodes || []).map((node: any) => {
        const nodeType = node.data?.type || node.type
        const nodeLabel = node.data?.label || node.label || nodeType
        const x = node.position?.x || 0
        const y = node.position?.y || 0
        const width = node.width || 180
        const height = node.height || 60
        
        // X6 使用 position 和 size 对象
        return {
          id: node.id,
          shape: getNodeShape(nodeType),
          position: { x, y },
          size: { width, height },
          label: nodeLabel,
          data: {
            ...node.data,
            type: nodeType,
            label: nodeLabel,
          },
        }
      })

      const edgeCells = (definition.edges || []).map((edge: any) => ({
        id: edge.id,
        shape: 'edge',
        source: { cell: edge.source, port: edge.source_handle },
        target: { cell: edge.target, port: edge.target_handle },
        labels: edge.label ? [{ attrs: { label: { text: edge.label } } }] : [],
        attrs: {
          line: {
            stroke: '#a0a0a0',
            strokeWidth: 2,
            targetMarker: { name: 'classic', size: 8 },
          },
        },
      }))

      return { cells: [...nodeCells, ...edgeCells] }
    }

    // 暴露方法给父组件
    useImperativeHandle(ref, () => ({
      addNode,
      getGraphData: () => {
        const graph = graphRef.current
        if (!graph) return { nodes: [], edges: [] }
        
        // 使用 toJSON() 获取画布数据，然后转换
        const rawData = graph.toJSON()
        return convertToWorkflowDefinition(rawData)
      },
      loadGraphData: (data: any) => {
        if (!graphRef.current) return
        // 清空现有画布
        graphRef.current.clearCells()
        // 转换并加载新数据
        const x6Data = convertFromWorkflowDefinition(data)
        graphRef.current.fromJSON(x6Data)
      },
      getGraph: () => graphRef.current,
    }))

    return (
      <div
        ref={containerRef}
        style={{
          width: '100%',
          height: '100%',
          overflow: 'hidden',
          background: '#fafafa',
        }}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault()
          const type = e.dataTransfer.getData('nodeType')
          const label = e.dataTransfer.getData('nodeLabel')
          
          if (type && graphRef.current && containerRef.current) {
            const rect = containerRef.current.getBoundingClientRect()
            const x = e.clientX - rect.left - 90 // 居中
            const y = e.clientY - rect.top - 30
            
            addNode(type, x, y, { label })
          }
        }}
      />
    )
  }
)

WorkflowCanvas.displayName = 'WorkflowCanvas'

export default WorkflowCanvas
