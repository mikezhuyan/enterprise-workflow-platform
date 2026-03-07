"""
组件服务 - 支持多种微服务协议
"""
import asyncio
import json
import httpx
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.component import Component, ComponentVersion, ComponentCategory, ComponentStatus
from app.schemas.component import ComponentCreate, ComponentUpdate, ComponentTestRequest
from app.core.config import settings


class ProtocolExecutor:
    """协议执行器 - 支持多种微服务协议"""
    
    @staticmethod
    async def execute_http(config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行HTTP/HTTPS请求"""
        method = config.get('method', 'GET').upper()
        url = config.get('url', '')
        headers = config.get('headers', {})
        timeout = config.get('timeout', 30)
        
        # 模板替换 - 将 {{variable}} 替换为实际值
        url = ProtocolExecutor._render_template(url, input_data)
        
        # 处理请求体
        body = None
        if method in ['POST', 'PUT', 'PATCH']:
            body_template = config.get('body', '{}')
            body = ProtocolExecutor._render_template(body_template, input_data)
            try:
                body = json.loads(body) if body else None
            except:
                pass
        
        # 处理查询参数
        params = config.get('params', {})
        if params:
            params = {k: ProtocolExecutor._render_template(str(v), input_data) for k, v in params.items()}
        
        async with httpx.AsyncClient(timeout=timeout, verify=config.get('verify_ssl', True)) as client:
            try:
                if method == 'GET':
                    response = await client.get(url, headers=headers, params=params)
                elif method == 'POST':
                    response = await client.post(url, headers=headers, json=body, params=params)
                elif method == 'PUT':
                    response = await client.put(url, headers=headers, json=body, params=params)
                elif method == 'DELETE':
                    response = await client.delete(url, headers=headers, params=params)
                elif method == 'PATCH':
                    response = await client.patch(url, headers=headers, json=body, params=params)
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")
                
                response.raise_for_status()
                
                # 尝试解析JSON响应
                try:
                    result = response.json()
                except:
                    result = {"text": response.text}
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "data": result,
                    "headers": dict(response.headers)
                }
            except httpx.HTTPStatusError as e:
                return {
                    "success": False,
                    "status_code": e.response.status_code,
                    "error": f"HTTP错误: {e.response.status_code}",
                    "detail": e.response.text
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
    
    @staticmethod
    async def execute_grpc(config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行gRPC调用 (简化实现)"""
        # gRPC需要grpcio库，这里提供接口框架
        return {
            "success": False,
            "error": "gRPC调用需要安装grpcio库，当前为演示模式",
            "note": "生产环境请安装: pip install grpcio grpcio-tools"
        }
    
    @staticmethod
    async def execute_graphql(config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行GraphQL查询"""
        url = config.get('url', '')
        query = config.get('query', '')
        variables = config.get('variables', {})
        headers = config.get('headers', {})
        headers['Content-Type'] = 'application/json'
        
        # 模板替换
        query = ProtocolExecutor._render_template(query, input_data)
        variables = {k: ProtocolExecutor._render_template(str(v), input_data) for k, v in variables.items()}
        
        payload = {
            "query": query,
            "variables": variables
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                
                if 'errors' in result:
                    return {
                        "success": False,
                        "error": "GraphQL错误",
                        "errors": result['errors']
                    }
                
                return {
                    "success": True,
                    "data": result.get('data', {})
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
    
    @staticmethod
    async def execute_soap(config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行SOAP调用"""
        url = config.get('url', '')
        soap_action = config.get('soap_action', '')
        soap_body = config.get('body', '')
        headers = config.get('headers', {})
        
        # 模板替换
        soap_body = ProtocolExecutor._render_template(soap_body, input_data)
        
        headers.update({
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': f'"{soap_action}"'
        })
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.post(url, headers=headers, content=soap_body)
                response.raise_for_status()
                
                # 尝试解析XML
                try:
                    root = ET.fromstring(response.text)
                    return {
                        "success": True,
                        "xml": response.text,
                        "parsed": ProtocolExecutor._xml_to_dict(root)
                    }
                except:
                    return {
                        "success": True,
                        "xml": response.text
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
    
    @staticmethod
    async def execute_websocket(config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行WebSocket通信 (简化实现)"""
        return {
            "success": False,
            "error": "WebSocket需要websockets库，当前为演示模式",
            "note": "生产环境请安装: pip install websockets"
        }
    
    @staticmethod
    async def execute_database(config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据库操作 (简化实现)"""
        # 支持 protocol 或 db_type 作为数据库类型
        db_type = config.get('protocol') or config.get('db_type', 'postgresql')
        connection_string = config.get('connection_string', '')
        sql = config.get('sql', '')
        
        # 模板替换
        sql = ProtocolExecutor._render_template(sql, input_data)
        
        # 如果没有提供连接字符串，返回错误
        if not connection_string:
            return {
                "success": False,
                "error": "缺少数据库连接字符串 (connection_string)"
            }
        
        # 如果没有提供SQL语句，返回错误
        if not sql:
            return {
                "success": False,
                "error": "缺少SQL语句 (sql)"
            }
        
        return {
            "success": True,
            "note": "数据库操作为演示模式",
            "sql": sql,
            "db_type": db_type,
            "connection_string": connection_string[:20] + "..." if len(connection_string) > 20 else connection_string
        }
    
    @staticmethod
    async def execute_message_queue(config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行消息队列操作 (简化实现)"""
        mq_type = config.get('mq_type', 'kafka')
        topic = config.get('topic', '')
        message = config.get('message', '')
        
        # 模板替换
        message = ProtocolExecutor._render_template(message, input_data)
        
        return {
            "success": True,
            "note": "消息队列为演示模式",
            "mq_type": mq_type,
            "topic": topic,
            "message": message
        }
    
    @staticmethod
    async def execute_script(config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行脚本"""
        language = config.get('language', 'python')
        code = config.get('code', '')
        
        # 对于演示，返回模拟结果
        return {
            "success": True,
            "note": f"{language}脚本执行为演示模式",
            "input": input_data,
            "output": {"result": "脚本执行结果", "language": language}
        }
    
    @staticmethod
    def _render_template(template: str, data: Dict[str, Any]) -> str:
        """简单的模板渲染 {{variable}}"""
        result = template
        for key, value in data.items():
            placeholder = "{{" + key + "}}"
            result = result.replace(placeholder, str(value))
        return result
    
    @staticmethod
    def _xml_to_dict(element: ET.Element) -> Any:
        """将XML元素转换为字典"""
        result = {}
        for child in element:
            child_data = ProtocolExecutor._xml_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        text = element.text.strip() if element.text else ''
        if text:
            if result:
                result['#text'] = text
            else:
                return text
        
        return result
    
    @classmethod
    async def execute(cls, component_type: str, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """根据组件类型执行相应的协议"""
        protocol = config.get('protocol', 'http').lower()
        
        if component_type == 'api':
            if protocol in ['http', 'https']:
                return await cls.execute_http(config, input_data)
            elif protocol == 'grpc':
                return await cls.execute_grpc(config, input_data)
            elif protocol == 'graphql':
                return await cls.execute_graphql(config, input_data)
            elif protocol == 'soap':
                return await cls.execute_soap(config, input_data)
            elif protocol == 'websocket':
                return await cls.execute_websocket(config, input_data)
            else:
                return {"success": False, "error": f"不支持的协议: {protocol}"}
        
        elif component_type == 'database':
            return await cls.execute_database(config, input_data)
        
        elif component_type == 'message':
            return await cls.execute_message_queue(config, input_data)
        
        elif component_type == 'script':
            return await cls.execute_script(config, input_data)
        
        else:
            return {"success": False, "error": f"不支持的组件类型: {component_type}"}


class ComponentService:
    """组件服务"""
    
    @staticmethod
    def get_by_id(db: Session, component_id: UUID) -> Optional[Component]:
        """根据ID获取组件"""
        return db.query(Component).filter(Component.id == component_id).first()
    
    @staticmethod
    def get_by_code(db: Session, code: str) -> Optional[Component]:
        """根据编码获取组件"""
        return db.query(Component).filter(Component.code == code).first()
    
    @staticmethod
    def list_components(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        component_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple:
        """获取组件列表"""
        query = db.query(Component)
        
        if component_type:
            query = query.filter(Component.component_type == component_type)
        
        if status:
            query = query.filter(Component.status == status)
        
        if search:
            query = query.filter(
                Component.name.ilike(f"%{search}%") |
                Component.code.ilike(f"%{search}%") |
                Component.description.ilike(f"%{search}%")
            )
        
        total = query.count()
        components = query.offset(skip).limit(limit).all()
        return components, total
    
    @staticmethod
    def create_component(db: Session, component_data: ComponentCreate, user_id) -> Component:
        """创建组件"""
        # 检查编码是否已存在
        existing = ComponentService.get_by_code(db, component_data.code)
        if existing:
            raise ValueError(f"组件编码已存在: {component_data.code}")
        
        # 确保 user_id 是 UUID 对象或字符串
        from uuid import UUID
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        
        db_component = Component(
            name=component_data.name,
            code=component_data.code,
            description=component_data.description,
            component_type=component_data.component_type,
            icon=component_data.icon,
            color=component_data.color,
            category_id=component_data.category_id,
            tags=component_data.tags or [],
            input_schema=component_data.input_schema.model_dump() if component_data.input_schema else {},
            output_schema=component_data.output_schema.model_dump() if component_data.output_schema else {},
            config_schema=component_data.config_schema.model_dump() if component_data.config_schema else {},
            execution_config=component_data.execution_config or {},
            implementation=component_data.implementation,
            language=component_data.language,
            documentation=component_data.documentation,
            examples=component_data.examples or [],
            visibility=component_data.visibility,
            created_by=user_id,
        )
        
        db.add(db_component)
        db.commit()
        db.refresh(db_component)
        return db_component
    
    @staticmethod
    def update_component(db: Session, component: Component, component_data: ComponentUpdate) -> Component:
        """更新组件"""
        update_data = component_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if field in ['input_schema', 'output_schema', 'config_schema'] and value is not None:
                # 只有Pydantic模型才需要调用model_dump()
                if hasattr(value, 'model_dump'):
                    value = value.model_dump()
            setattr(component, field, value)
        
        component.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(component)
        return component
    
    @staticmethod
    def delete_component(db: Session, component: Component) -> None:
        """删除组件"""
        db.delete(component)
        db.commit()
    
    @staticmethod
    async def test_component(
        db: Session,
        component: Component,
        test_data: ComponentTestRequest
    ) -> Dict[str, Any]:
        """测试组件"""
        start_time = datetime.utcnow()
        
        try:
            # 执行组件
            result = await ProtocolExecutor.execute(
                component.component_type,
                component.execution_config,
                test_data.input_data
            )
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return {
                "success": result.get("success", False),
                "output_data": result,
                "duration_ms": int(duration),
                "logs": [f"[{start_time.isoformat()}] 组件测试开始", f"[{datetime.utcnow().isoformat()}] 组件测试完成"]
            }
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            return {
                "success": False,
                "error_message": str(e),
                "duration_ms": int(duration),
                "logs": [f"[{start_time.isoformat()}] 组件测试开始", f"[ERROR] {str(e)}"]
            }
    
    @staticmethod
    def publish_component(db: Session, component: Component) -> Component:
        """发布组件"""
        component.status = ComponentStatus.PUBLISHED.value
        component.published_at = datetime.utcnow()
        db.commit()
        db.refresh(component)
        return component


class ComponentCategoryService:
    """组件分类服务"""
    
    @staticmethod
    def get_categories(db: Session) -> List[ComponentCategory]:
        """获取所有分类"""
        return db.query(ComponentCategory).order_by(ComponentCategory.sort_order).all()
    
    @staticmethod
    def create_category(db: Session, name: str, code: str, **kwargs) -> ComponentCategory:
        """创建分类"""
        category = ComponentCategory(name=name, code=code, **kwargs)
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
