"""
工作流引擎核心
支持传统组件和AI组件的执行
"""
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid


class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class NodeType(str, Enum):
    # 传统组件
    API = "api"
    DATABASE = "database"
    MESSAGE = "message"
    SCRIPT = "script"
    CONDITION = "condition"
    LOOP = "loop"
    DELAY = "delay"
    SUBFLOW = "subflow"
    
    # AI组件
    LLM = "llm"
    AGENT = "agent"
    MCP = "mcp"
    
    # 控制流
    START = "start"
    END = "end"
    PARALLEL = "parallel"


@dataclass
class NodeExecutionResult:
    """节点执行结果"""
    node_id: str
    status: NodeStatus
    output: Any = None
    error: Optional[str] = None
    duration_ms: int = 0
    logs: List[str] = field(default_factory=list)


@dataclass
class ExecutionContext:
    """执行上下文"""
    workflow_id: str
    execution_id: str
    variables: Dict[str, Any] = field(default_factory=dict)
    node_outputs: Dict[str, Any] = field(default_factory=dict)
    execution_path: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_variable(self, name: str, default=None):
        """获取变量值"""
        return self.variables.get(name, default)
    
    def set_variable(self, name: str, value: Any):
        """设置变量值"""
        self.variables[name] = value
    
    def set_node_output(self, node_id: str, output: Any):
        """设置节点输出"""
        self.node_outputs[node_id] = output
    
    def get_node_output(self, node_id: str):
        """获取节点输出"""
        return self.node_outputs.get(node_id)


class WorkflowNodeExecutor:
    """工作流节点执行器"""
    
    def __init__(self):
        self.handlers: Dict[str, Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认处理器"""
        self.handlers[NodeType.START] = self._handle_start
        self.handlers[NodeType.END] = self._handle_end
        self.handlers[NodeType.API] = self._handle_api
        self.handlers[NodeType.CONDITION] = self._handle_condition
        self.handlers[NodeType.DELAY] = self._handle_delay
        self.handlers[NodeType.LLM] = self._handle_llm
        self.handlers[NodeType.MCP] = self._handle_mcp
        self.handlers[NodeType.AGENT] = self._handle_agent
    
    async def execute(self, node: Dict[str, Any], context: ExecutionContext) -> NodeExecutionResult:
        """执行节点"""
        node_id = node["id"]
        node_type = node.get("type", "unknown")
        node_data = node.get("data", {})
        
        start_time = datetime.utcnow()
        logs = []
        
        try:
            handler = self.handlers.get(node_type)
            if not handler:
                raise ValueError(f"未知的节点类型: {node_type}")
            
            logs.append(f"[{node_type}] 开始执行节点: {node_id}")
            
            # 准备输入数据
            input_data = self._prepare_input(node_data, context)
            
            # 执行处理器
            output = await handler(node_data, input_data, context, logs)
            
            # 保存节点输出到上下文
            context.set_node_output(node_id, output)
            
            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            logs.append(f"[{node_type}] 节点执行成功，耗时: {duration}ms")
            
            return NodeExecutionResult(
                node_id=node_id,
                status=NodeStatus.SUCCESS,
                output=output,
                duration_ms=duration,
                logs=logs
            )
            
        except Exception as e:
            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            logs.append(f"[{node_type}] 节点执行失败: {str(e)}")
            
            return NodeExecutionResult(
                node_id=node_id,
                status=NodeStatus.FAILED,
                error=str(e),
                duration_ms=duration,
                logs=logs
            )
    
    def _prepare_input(self, node_data: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """准备节点输入数据"""
        input_config = node_data.get("input", {})
        result = {}
        
        for key, config in input_config.items():
            source = config.get("source", "static")  # static, variable, node
            value = config.get("value")
            
            if source == "variable":
                result[key] = context.get_variable(value)
            elif source == "node":
                result[key] = context.get_node_output(value)
            else:
                result[key] = value
        
        return result
    
    # ============ 节点处理器 ============
    
    async def _handle_start(self, node_data: Dict, input_data: Dict, context: ExecutionContext, logs: List[str]) -> Any:
        """处理开始节点"""
        logs.append("工作流开始执行")
        return {"started_at": datetime.utcnow().isoformat()}
    
    async def _handle_end(self, node_data: Dict, input_data: Dict, context: ExecutionContext, logs: List[str]) -> Any:
        """处理结束节点"""
        logs.append("工作流执行完成")
        return {
            "completed_at": datetime.utcnow().isoformat(),
            "variables": context.variables,
            "outputs": context.node_outputs
        }
    
    async def _handle_api(self, node_data: Dict, input_data: Dict, context: ExecutionContext, logs: List[str]) -> Any:
        """处理API节点"""
        import httpx
        
        config = node_data.get("api_config", {})
        method = config.get("method", "GET")
        url = config.get("url", "")
        headers = config.get("headers", {})
        timeout = config.get("timeout", 30)
        
        logs.append(f"发起 {method} 请求到 {url}")
        
        async with httpx.AsyncClient() as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, timeout=timeout)
                elif method.upper() == "POST":
                    response = await client.post(url, json=input_data, headers=headers, timeout=timeout)
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")
                
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                raise Exception(f"API请求失败: {str(e)}")
    
    async def _handle_condition(self, node_data: Dict, input_data: Dict, context: ExecutionContext, logs: List[str]) -> Any:
        """处理条件节点"""
        conditions = node_data.get("conditions", [])
        
        for condition in conditions:
            expression = condition.get("expression", "")
            # 简化的条件评估
            try:
                result = eval(expression, {"input": input_data, "var": context.variables})
                logs.append(f"条件评估: {expression} = {result}")
                if result:
                    return {"condition_met": True, "matched_condition": condition}
            except Exception as e:
                logs.append(f"条件评估失败: {e}")
        
        return {"condition_met": False}
    
    async def _handle_delay(self, node_data: Dict, input_data: Dict, context: ExecutionContext, logs: List[str]) -> Any:
        """处理延时节点"""
        delay_ms = node_data.get("delay_ms", 1000)
        logs.append(f"延时 {delay_ms}ms")
        await asyncio.sleep(delay_ms / 1000)
        return {"delayed_ms": delay_ms}
    
    async def _handle_llm(self, node_data: Dict, input_data: Dict, context: ExecutionContext, logs: List[str]) -> Any:
        """处理LLM节点"""
        model = node_data.get("model", "gpt-4")
        prompt = node_data.get("prompt", "")
        temperature = node_data.get("temperature", 0.7)
        
        logs.append(f"调用LLM模型: {model}")
        
        # 这里是简化实现，实际需要集成OpenAI或其他LLM服务
        # 返回模拟响应
        return {
            "model": model,
            "content": f"LLM响应: 收到输入 {json.dumps(input_data)}",
            "usage": {"prompt_tokens": 100, "completion_tokens": 50}
        }
    
    async def _handle_mcp(self, node_data: Dict, input_data: Dict, context: ExecutionContext, logs: List[str]) -> Any:
        """处理MCP节点"""
        server_name = node_data.get("server_name", "")
        tool_name = node_data.get("tool_name", "")
        
        logs.append(f"调用MCP工具: {server_name}.{tool_name}")
        
        # MCP调用需要实现MCP客户端
        return {
            "server": server_name,
            "tool": tool_name,
            "result": "MCP工具执行结果"
        }
    
    async def _handle_agent(self, node_data: Dict, input_data: Dict, context: ExecutionContext, logs: List[str]) -> Any:
        """处理Agent节点"""
        agent_id = node_data.get("agent_id", "")
        skill_codes = node_data.get("skills", [])
        
        logs.append(f"调用Agent: {agent_id}, 技能: {skill_codes}")
        
        return {
            "agent_id": agent_id,
            "executed_skills": skill_codes,
            "result": "Agent执行结果"
        }


class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self):
        self.node_executor = WorkflowNodeExecutor()
        self.running_executions: Dict[str, asyncio.Task] = {}
    
    async def execute_workflow(
        self,
        workflow_definition: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """执行工作流"""
        execution_id = execution_id or str(uuid.uuid4())
        
        # 创建工作流定义
        nodes = {n["id"]: n for n in workflow_definition.get("nodes", [])}
        edges = workflow_definition.get("edges", [])
        
        # 构建连接图
        connections = self._build_connections(nodes, edges)
        
        # 创建执行上下文
        context = ExecutionContext(
            workflow_id=workflow_definition.get("id"),
            execution_id=execution_id,
            variables=input_data.copy()
        )
        
        # 执行结果
        results = []
        
        # 找到开始节点
        start_node = self._find_start_node(nodes)
        if not start_node:
            raise ValueError("工作流缺少开始节点")
        
        # 执行工作流
        try:
            await self._execute_node_recursive(
                start_node, nodes, connections, context, results
            )
            
            return {
                "execution_id": execution_id,
                "status": "success",
                "results": results,
                "context": {
                    "variables": context.variables,
                    "outputs": context.node_outputs
                }
            }
        except Exception as e:
            return {
                "execution_id": execution_id,
                "status": "failed",
                "error": str(e),
                "results": results
            }
    
    def _build_connections(self, nodes: Dict, edges: List[Dict]) -> Dict[str, List[str]]:
        """构建节点连接图"""
        connections = {node_id: [] for node_id in nodes}
        
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source and target:
                connections[source].append(target)
        
        return connections
    
    def _find_start_node(self, nodes: Dict) -> Optional[Dict]:
        """找到开始节点"""
        for node in nodes.values():
            if node.get("type") == NodeType.START:
                return node
        # 如果没有明确的开始节点，返回第一个节点
        return next(iter(nodes.values())) if nodes else None
    
    async def _execute_node_recursive(
        self,
        node: Dict,
        nodes: Dict,
        connections: Dict[str, List[str]],
        context: ExecutionContext,
        results: List[NodeExecutionResult]
    ):
        """递归执行节点"""
        node_id = node["id"]
        context.execution_path.append(node_id)
        
        # 执行当前节点
        result = await self.node_executor.execute(node, context)
        results.append(result)
        
        if result.status == NodeStatus.FAILED:
            raise Exception(f"节点 {node_id} 执行失败: {result.error}")
        
        # 获取下一个节点
        next_node_ids = connections.get(node_id, [])
        
        # 处理条件分支
        if node.get("type") == NodeType.CONDITION:
            condition_met = result.output.get("condition_met", False)
            matched_condition = result.output.get("matched_condition", {})
            
            if matched_condition:
                target_id = matched_condition.get("target")
                if target_id and target_id in nodes:
                    await self._execute_node_recursive(
                        nodes[target_id], nodes, connections, context, results
                    )
                    return
        
        # 顺序执行下一个节点
        for next_id in next_node_ids:
            if next_id in nodes:
                await self._execute_node_recursive(
                    nodes[next_id], nodes, connections, context, results
                )
    
    def cancel_execution(self, execution_id: str) -> bool:
        """取消执行"""
        task = self.running_executions.get(execution_id)
        if task and not task.done():
            task.cancel()
            return True
        return False
