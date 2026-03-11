"""
工作流服务
"""
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
import difflib
import json

from app.models.workflow import (
    Workflow, WorkflowExecution, NodeExecution, ExecutionLog,
    WorkflowCategory, WorkflowSchedule, WorkflowStatus, ExecutionStatus
)
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate


class WorkflowService:
    """工作流服务"""
    
    @staticmethod
    def get_by_id(db: Session, workflow_id: UUID) -> Optional[Workflow]:
        """根据ID获取工作流"""
        return db.query(Workflow).filter(Workflow.id == workflow_id).first()
    
    @staticmethod
    def list_workflows(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        category_id: Optional[UUID] = None,
        status: Optional[str] = None,
        tenant_id: Optional[UUID] = None
    ) -> tuple:
        """获取工作流列表"""
        query = db.query(Workflow)
        
        if tenant_id:
            query = query.filter(Workflow.tenant_id == tenant_id)
        
        if category_id:
            query = query.filter(Workflow.category_id == category_id)
        
        if status:
            query = query.filter(Workflow.status == status)
        
        if search:
            query = query.filter(
                Workflow.name.ilike(f"%{search}%") |
                Workflow.description.ilike(f"%{search}%")
            )
        
        total = query.count()
        workflows = query.order_by(Workflow.created_at.desc()).offset(skip).limit(limit).all()
        return workflows, total
    
    @staticmethod
    def create_workflow(db: Session, workflow_data: WorkflowCreate, user_id: UUID, tenant_id: Optional[UUID] = None) -> Workflow:
        """创建工作流"""
        # 处理definition，支持Pydantic模型或字典
        definition = workflow_data.definition
        if hasattr(definition, 'model_dump'):
            definition = definition.model_dump()
        elif definition is None:
            definition = {"nodes": [], "edges": []}
        
        db_workflow = Workflow(
            name=workflow_data.name,
            description=workflow_data.description,
            version="1.0.0",
            status=WorkflowStatus.DRAFT.value,
            is_template=workflow_data.is_template,
            definition=definition,
            variables=[v.model_dump() for v in workflow_data.variables] if workflow_data.variables else [],
            triggers=[t.model_dump() for t in workflow_data.triggers] if workflow_data.triggers else [],
            category_id=workflow_data.category_id,
            tags=workflow_data.tags or [],
            created_by=user_id,
            tenant_id=tenant_id,
        )
        
        db.add(db_workflow)
        db.commit()
        db.refresh(db_workflow)
        return db_workflow
    
    @staticmethod
    def update_workflow(db: Session, workflow: Workflow, workflow_data: WorkflowUpdate) -> Workflow:
        """更新工作流"""
        update_data = workflow_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if field in ['definition', 'variables', 'triggers'] and value is not None:
                if field == 'definition':
                    # 支持Pydantic模型或字典
                    if hasattr(value, 'model_dump'):
                        value = value.model_dump()
                    # 如果是字典，直接使用
                elif field in ['variables', 'triggers']:
                    # 处理列表中的每个元素
                    value = [v.model_dump() if hasattr(v, 'model_dump') else v for v in value]
            setattr(workflow, field, value)
        
        workflow.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(workflow)
        return workflow
    
    @staticmethod
    def delete_workflow(db: Session, workflow: Workflow) -> None:
        """删除工作流"""
        db.delete(workflow)
        db.commit()
    
    @staticmethod
    def publish_workflow(db: Session, workflow: Workflow, version: Optional[str] = None) -> Workflow:
        """发布工作流"""
        if version:
            workflow.version = version
        else:
            # 自动递增版本号
            parts = workflow.version.split('.')
            parts[-1] = str(int(parts[-1]) + 1)
            workflow.version = '.'.join(parts)
        
        workflow.status = WorkflowStatus.PUBLISHED.value
        workflow.published_at = datetime.utcnow()
        db.commit()
        db.refresh(workflow)
        return workflow
    
    @staticmethod
    def get_execution_by_id(db: Session, execution_id: UUID) -> Optional[WorkflowExecution]:
        """根据ID获取执行记录"""
        return db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
    
    @staticmethod
    def list_executions(
        db: Session,
        workflow_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None
    ) -> tuple:
        """获取执行记录列表"""
        query = db.query(WorkflowExecution).filter(WorkflowExecution.workflow_id == workflow_id)
        
        if status:
            query = query.filter(WorkflowExecution.status == status)
        
        total = query.count()
        executions = query.order_by(WorkflowExecution.created_at.desc()).offset(skip).limit(limit).all()
        return executions, total
    
    @staticmethod
    def create_execution(db: Session, workflow_id: UUID, input_data: Dict, triggered_by: Optional[UUID] = None) -> WorkflowExecution:
        """创建执行记录"""
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            status=ExecutionStatus.PENDING.value,
            input_data=input_data,
            triggered_by=triggered_by,
            trigger_type="manual",
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        return execution

    # ============ 版本控制方法 ============

    @staticmethod
    def _increment_version(version: str, level: str = "minor") -> str:
        """
        递增版本号
        
        Args:
            version: 当前版本号 (如 1.0.0)
            level: 递增级别 (major, minor, patch)
        
        Returns:
            新版本号
        """
        parts = version.split(".")
        if len(parts) != 3:
            parts = ["1", "0", "0"]
        
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        
        if level == "major":
            major += 1
            minor = 0
            patch = 0
        elif level == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1
        
        return f"{major}.{minor}.{patch}"

    @staticmethod
    def create_version(
        db: Session,
        workflow: Workflow,
        version_type: str = "minor",
        comment: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> Workflow:
        """
        创建新版本
        
        复制现有工作流的所有配置，创建一个新版本记录
        
        Args:
            db: 数据库会话
            workflow: 现有工作流
            version_type: 版本递增类型 (major, minor, patch)
            comment: 版本说明
            user_id: 创建者ID
        
        Returns:
            新创建的工作流版本
        """
        # 生成新版本号
        new_version = WorkflowService._increment_version(workflow.version, version_type)
        
        # 创建新版本工作流
        new_workflow = Workflow(
            name=workflow.name,
            description=workflow.description,
            version=new_version,
            parent_id=workflow.id,  # 指向原始工作流
            status=WorkflowStatus.DRAFT.value,
            is_template=workflow.is_template,
            definition=workflow.definition,
            variables=workflow.variables,
            triggers=workflow.triggers,
            category_id=workflow.category_id,
            tags=workflow.tags,
            created_by=user_id or workflow.created_by,
            tenant_id=workflow.tenant_id,
        )
        
        db.add(new_workflow)
        db.commit()
        db.refresh(new_workflow)
        
        # 将版本说明存储在 definition 中
        if comment:
            new_workflow.definition = {
                **(new_workflow.definition or {}),
                "_version_comment": comment
            }
            db.commit()
        
        return new_workflow

    @staticmethod
    def get_versions(
        db: Session,
        workflow_id: UUID,
        include_parent: bool = True
    ) -> List[Workflow]:
        """
        获取工作流的所有版本
        
        Args:
            db: 数据库会话
            workflow_id: 工作流ID
            include_parent: 是否包含父工作流
        
        Returns:
            版本列表，按版本号降序排列
        """
        workflow = WorkflowService.get_by_id(db, workflow_id)
        if not workflow:
            return []
        
        # 获取根工作流ID（最原始的版本）
        root_id = workflow_id
        if workflow.parent_id:
            root_id = workflow.parent_id
            # 继续向上查找根
            while True:
                parent = WorkflowService.get_by_id(db, root_id)
                if parent and parent.parent_id:
                    root_id = parent.parent_id
                else:
                    break
        
        # 获取所有版本（包括根和子版本）
        versions = []
        
        if include_parent:
            # 获取根工作流
            root = WorkflowService.get_by_id(db, root_id)
            if root:
                versions.append(root)
        
        # 递归获取所有子版本
        def get_children(parent_id: UUID):
            children = db.query(Workflow).filter(
                Workflow.parent_id == parent_id
            ).all()
            for child in children:
                versions.append(child)
                get_children(child.id)
        
        get_children(root_id)
        
        # 按版本号降序排序
        def version_key(w: Workflow):
            parts = w.version.split(".")
            return tuple(int(p) for p in parts)
        
        versions.sort(key=version_key, reverse=True)
        
        return versions

    @staticmethod
    def get_version_by_number(
        db: Session,
        workflow_id: UUID,
        version: str
    ) -> Optional[Workflow]:
        """
        根据版本号获取指定版本
        
        Args:
            db: 数据库会话
            workflow_id: 工作流ID
            version: 版本号 (如 1.0.0)
        
        Returns:
            指定版本的工作流
        """
        workflow = WorkflowService.get_by_id(db, workflow_id)
        if not workflow:
            return None
        
        # 获取根工作流ID
        root_id = workflow_id
        if workflow.parent_id:
            root_id = workflow.parent_id
            while True:
                parent = WorkflowService.get_by_id(db, root_id)
                if parent and parent.parent_id:
                    root_id = parent.parent_id
                else:
                    break
        
        # 在所有版本中查找指定版本号
        all_versions = WorkflowService.get_versions(db, root_id)
        for v in all_versions:
            if v.version == version:
                return v
        
        return None

    @staticmethod
    def rollback_to_version(
        db: Session,
        workflow_id: UUID,
        target_version: str,
        user_id: Optional[UUID] = None
    ) -> Optional[Workflow]:
        """
        回滚到指定版本
        
        创建一个新版本，其内容与目标版本相同
        
        Args:
            db: 数据库会话
            workflow_id: 当前工作流ID
            target_version: 目标版本号
            user_id: 执行回滚的用户ID
        
        Returns:
            回滚后创建的新版本
        """
        # 获取当前工作流
        current_workflow = WorkflowService.get_by_id(db, workflow_id)
        if not current_workflow:
            return None
        
        # 获取目标版本
        target = WorkflowService.get_version_by_number(db, workflow_id, target_version)
        if not target:
            return None
        
        # 生成新版本号
        new_version = WorkflowService._increment_version(current_workflow.version, "patch")
        
        # 创建回滚版本（复制目标版本的配置）
        rollback_workflow = Workflow(
            name=current_workflow.name,
            description=f"回滚到版本 {target_version}",
            version=new_version,
            parent_id=workflow_id,
            status=WorkflowStatus.DRAFT.value,
            is_template=current_workflow.is_template,
            definition=target.definition,
            variables=target.variables,
            triggers=target.triggers,
            category_id=current_workflow.category_id,
            tags=current_workflow.tags,
            created_by=user_id or current_workflow.created_by,
            tenant_id=current_workflow.tenant_id,
        )
        
        db.add(rollback_workflow)
        db.commit()
        db.refresh(rollback_workflow)
        
        # 标记为回滚版本
        rollback_workflow.definition = {
            **(rollback_workflow.definition or {}),
            "_version_comment": f"回滚到版本 {target_version}",
            "_rollback_from": current_workflow.version,
            "_rollback_to": target_version
        }
        db.commit()
        
        return rollback_workflow

    @staticmethod
    def compare_versions(
        db: Session,
        workflow_id: UUID,
        version1: str,
        version2: str
    ) -> Dict[str, Any]:
        """
        比较两个版本的差异
        
        Args:
            db: 数据库会话
            workflow_id: 工作流ID
            version1: 第一个版本号
            version2: 第二个版本号
        
        Returns:
            差异信息
        """
        import difflib
        import json

        w1 = WorkflowService.get_version_by_number(db, workflow_id, version1)
        w2 = WorkflowService.get_version_by_number(db, workflow_id, version2)
        
        if not w1 or not w2:
            return {"error": "版本不存在"}
        
        # 比较各个字段
        differences = {
            "version1": version1,
            "version2": version2,
            "workflow_id": str(workflow_id),
            "changes": []
        }
        
        # 比较名称
        if w1.name != w2.name:
            differences["changes"].append({
                "field": "name",
                "type": "modified",
                "old": w1.name,
                "new": w2.name
            })
        
        # 比较描述
        if w1.description != w2.description:
            differences["changes"].append({
                "field": "description",
                "type": "modified",
                "old": w1.description,
                "new": w2.description
            })
        
        # 比较状态
        if w1.status != w2.status:
            differences["changes"].append({
                "field": "status",
                "type": "modified",
                "old": w1.status,
                "new": w2.status
            })
        
        # 比较 definition (节点和边)
        def1 = w1.definition or {}
        def2 = w2.definition or {}
        
        # 移除内部字段进行比较
        def1_clean = {k: v for k, v in def1.items() if not k.startswith("_")}
        def2_clean = {k: v for k, v in def2.items() if not k.startswith("_")}
        
        node_changes = []
        edge_changes = []

        if def1_clean != def2_clean:
            # 比较节点
            nodes1 = {n.get("id"): n for n in def1_clean.get("nodes", [])}
            nodes2 = {n.get("id"): n for n in def2_clean.get("nodes", [])}
            
            # 新增的节点
            for node_id in nodes2:
                if node_id not in nodes1:
                    node_changes.append({
                        "type": "added",
                        "node": nodes2[node_id]
                    })
            
            # 删除的节点
            for node_id in nodes1:
                if node_id not in nodes2:
                    node_changes.append({
                        "type": "removed",
                        "node": nodes1[node_id]
                    })
            
            # 修改的节点
            for node_id in nodes1:
                if node_id in nodes2 and nodes1[node_id] != nodes2[node_id]:
                    node_changes.append({
                        "type": "modified",
                        "node_id": node_id,
                        "old": nodes1[node_id],
                        "new": nodes2[node_id]
                    })
            
            # 比较边
            edges1 = {(e.get("source"), e.get("target")): e for e in def1_clean.get("edges", [])}
            edges2 = {(e.get("source"), e.get("target")): e for e in def2_clean.get("edges", [])}
            
            # 新增的边
            for edge_key in edges2:
                if edge_key not in edges1:
                    edge_changes.append({
                        "type": "added",
                        "edge": edges2[edge_key]
                    })
            
            # 删除的边
            for edge_key in edges1:
                if edge_key not in edges2:
                    edge_changes.append({
                        "type": "removed",
                        "edge": edges1[edge_key]
                    })
            
            if node_changes or edge_changes:
                differences["changes"].append({
                    "field": "definition",
                    "type": "modified",
                    "node_changes": node_changes,
                    "edge_changes": edge_changes
                })
        
        # 比较变量
        vars1 = w1.variables or []
        vars2 = w2.variables or []
        if vars1 != vars2:
            differences["changes"].append({
                "field": "variables",
                "type": "modified",
                "old": vars1,
                "new": vars2
            })
        
        # 比较触发器
        triggers1 = w1.triggers or []
        triggers2 = w2.triggers or []
        if triggers1 != triggers2:
            differences["changes"].append({
                "field": "triggers",
                "type": "modified",
                "old": triggers1,
                "new": triggers2
            })
        
        # 比较标签
        tags1 = set(w1.tags or [])
        tags2 = set(w2.tags or [])
        if tags1 != tags2:
            added_tags = list(tags2 - tags1)
            removed_tags = list(tags1 - tags2)
            differences["changes"].append({
                "field": "tags",
                "type": "modified",
                "added": added_tags,
                "removed": removed_tags
            })
        
        # 生成文本差异
        def1_json = json.dumps(def1_clean, indent=2, ensure_ascii=False, sort_keys=True)
        def2_json = json.dumps(def2_clean, indent=2, ensure_ascii=False, sort_keys=True)
        
        diff_lines = list(difflib.unified_diff(
            def1_json.splitlines(keepends=True),
            def2_json.splitlines(keepends=True),
            fromfile=f"version {version1}",
            tofile=f"version {version2}"
        ))
        
        differences["diff_text"] = "".join(diff_lines)
        differences["summary"] = {
            "total_changes": len(differences["changes"]),
            "nodes_added": len([c for c in node_changes if c["type"] == "added"]),
            "nodes_removed": len([c for c in node_changes if c["type"] == "removed"]),
            "nodes_modified": len([c for c in node_changes if c["type"] == "modified"]),
            "edges_added": len([c for c in edge_changes if c["type"] == "added"]),
            "edges_removed": len([c for c in edge_changes if c["type"] == "removed"])
        }
        
        return differences


class WorkflowCategoryService:
    """工作流分类服务"""
    
    @staticmethod
    def get_categories(db: Session) -> List[WorkflowCategory]:
        """获取所有分类"""
        return db.query(WorkflowCategory).order_by(WorkflowCategory.sort_order).all()
    
    @staticmethod
    def create_category(db: Session, name: str, **kwargs) -> WorkflowCategory:
        """创建分类"""
        category = WorkflowCategory(name=name, **kwargs)
        db.add(category)
        db.commit()
        db.refresh(category)
        return category


    @staticmethod
    def _increment_version(version: str, level: str = "minor") -> str:
        """
        递增版本号
        
        Args:
            version: 当前版本号 (如 1.0.0)
            level: 递增级别 (major, minor, patch)
        
        Returns:
            新版本号
        """
        parts = version.split(".")
        if len(parts) != 3:
            parts = ["1", "0", "0"]
        
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        
        if level == "major":
            major += 1
            minor = 0
            patch = 0
        elif level == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1
        
        return f"{major}.{minor}.{patch}"

    @staticmethod
    def create_version(
        db: Session,
        workflow: Workflow,
        version_type: str = "minor",
        comment: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> Workflow:
        """
        创建新版本
        
        复制现有工作流的所有配置，创建一个新版本记录
        
        Args:
            db: 数据库会话
            workflow: 现有工作流
            version_type: 版本递增类型 (major, minor, patch)
            comment: 版本说明
            user_id: 创建者ID
        
        Returns:
            新创建的工作流版本
        """
        # 生成新版本号
        new_version = WorkflowService._increment_version(workflow.version, version_type)
        
        # 创建新版本工作流
        new_workflow = Workflow(
            name=workflow.name,
            description=workflow.description,
            version=new_version,
            parent_id=workflow.id,  # 指向原始工作流
            status=WorkflowStatus.DRAFT.value,
            is_template=workflow.is_template,
            definition=workflow.definition,
            variables=workflow.variables,
            triggers=workflow.triggers,
            category_id=workflow.category_id,
            tags=workflow.tags,
            created_by=user_id or workflow.created_by,
            tenant_id=workflow.tenant_id,
        )
        
        db.add(new_workflow)
        db.commit()
        db.refresh(new_workflow)
        
        # 将版本说明存储在 definition 中
        if comment:
            new_workflow.definition = {
                **(new_workflow.definition or {}),
                "_version_comment": comment
            }
            db.commit()
        
        return new_workflow

    @staticmethod
    def get_versions(
        db: Session,
        workflow_id: UUID,
        include_parent: bool = True
    ) -> List[Workflow]:
        """
        获取工作流的所有版本
        
        Args:
            db: 数据库会话
            workflow_id: 工作流ID
            include_parent: 是否包含父工作流
        
        Returns:
            版本列表，按版本号降序排列
        """
        workflow = WorkflowService.get_by_id(db, workflow_id)
        if not workflow:
            return []
        
        # 获取根工作流ID（最原始的版本）
        root_id = workflow_id
        if workflow.parent_id:
            root_id = workflow.parent_id
            # 继续向上查找根
            while True:
                parent = WorkflowService.get_by_id(db, root_id)
                if parent and parent.parent_id:
                    root_id = parent.parent_id
                else:
                    break
        
        # 获取所有版本（包括根和子版本）
        versions = []
        
        if include_parent:
            # 获取根工作流
            root = WorkflowService.get_by_id(db, root_id)
            if root:
                versions.append(root)
        
        # 递归获取所有子版本
        def get_children(parent_id: UUID):
            children = db.query(Workflow).filter(
                Workflow.parent_id == parent_id
            ).all()
            for child in children:
                versions.append(child)
                get_children(child.id)
        
        get_children(root_id)
        
        # 按版本号降序排序
        def version_key(w: Workflow):
            parts = w.version.split(".")
            return tuple(int(p) for p in parts)
        
        versions.sort(key=version_key, reverse=True)
        
        return versions

    @staticmethod
    def get_version_by_number(
        db: Session,
        workflow_id: UUID,
        version: str
    ) -> Optional[Workflow]:
        """
        根据版本号获取指定版本
        
        Args:
            db: 数据库会话
            workflow_id: 工作流ID
            version: 版本号 (如 1.0.0)
        
        Returns:
            指定版本的工作流
        """
        workflow = WorkflowService.get_by_id(db, workflow_id)
        if not workflow:
            return None
        
        # 获取根工作流ID
        root_id = workflow_id
        if workflow.parent_id:
            root_id = workflow.parent_id
            while True:
                parent = WorkflowService.get_by_id(db, root_id)
                if parent and parent.parent_id:
                    root_id = parent.parent_id
                else:
                    break
        
        # 在所有版本中查找指定版本号
        all_versions = WorkflowService.get_versions(db, root_id)
        for v in all_versions:
            if v.version == version:
                return v
        
        return None

    @staticmethod
    def rollback_to_version(
        db: Session,
        workflow_id: UUID,
        target_version: str,
        user_id: Optional[UUID] = None
    ) -> Optional[Workflow]:
        """
        回滚到指定版本
        
        创建一个新版本，其内容与目标版本相同
        
        Args:
            db: 数据库会话
            workflow_id: 当前工作流ID
            target_version: 目标版本号
            user_id: 执行回滚的用户ID
        
        Returns:
            回滚后创建的新版本
        """
        # 获取当前工作流
        current_workflow = WorkflowService.get_by_id(db, workflow_id)
        if not current_workflow:
            return None
        
        # 获取目标版本
        target = WorkflowService.get_version_by_number(db, workflow_id, target_version)
        if not target:
            return None
        
        # 生成新版本号
        new_version = WorkflowService._increment_version(current_workflow.version, "patch")
        
        # 创建回滚版本（复制目标版本的配置）
        rollback_workflow = Workflow(
            name=current_workflow.name,
            description=f"回滚到版本 {target_version}",
            version=new_version,
            parent_id=workflow_id,
            status=WorkflowStatus.DRAFT.value,
            is_template=current_workflow.is_template,
            definition=target.definition,
            variables=target.variables,
            triggers=target.triggers,
            category_id=current_workflow.category_id,
            tags=current_workflow.tags,
            created_by=user_id or current_workflow.created_by,
            tenant_id=current_workflow.tenant_id,
        )
        
        db.add(rollback_workflow)
        db.commit()
        db.refresh(rollback_workflow)
        
        # 标记为回滚版本
        rollback_workflow.definition = {
            **(rollback_workflow.definition or {}),
            "_version_comment": f"回滚到版本 {target_version}",
            "_rollback_from": current_workflow.version,
            "_rollback_to": target_version
        }
        db.commit()
        
        return rollback_workflow

    @staticmethod
    def compare_versions(
        db: Session,
        workflow_id: UUID,
        version1: str,
        version2: str
    ) -> Dict[str, Any]:
        """
        比较两个版本的差异
        
        Args:
            db: 数据库会话
            workflow_id: 工作流ID
            version1: 第一个版本号
            version2: 第二个版本号
        
        Returns:
            差异信息
        """
        w1 = WorkflowService.get_version_by_number(db, workflow_id, version1)
        w2 = WorkflowService.get_version_by_number(db, workflow_id, version2)
        
        if not w1 or not w2:
            return {"error": "版本不存在"}
        
        # 比较各个字段
        differences = {
            "version1": version1,
            "version2": version2,
            "workflow_id": str(workflow_id),
            "changes": []
        }
        
        # 比较名称
        if w1.name != w2.name:
            differences["changes"].append({
                "field": "name",
                "type": "modified",
                "old": w1.name,
                "new": w2.name
            })
        
        # 比较描述
        if w1.description != w2.description:
            differences["changes"].append({
                "field": "description",
                "type": "modified",
                "old": w1.description,
                "new": w2.description
            })
        
        # 比较状态
        if w1.status != w2.status:
            differences["changes"].append({
                "field": "status",
                "type": "modified",
                "old": w1.status,
                "new": w2.status
            })
        
        # 比较 definition (节点和边)
        def1 = w1.definition or {}
        def2 = w2.definition or {}
        
        # 移除内部字段进行比较
        def1_clean = {k: v for k, v in def1.items() if not k.startswith("_")}
        def2_clean = {k: v for k, v in def2.items() if not k.startswith("_")}
        
        if def1_clean != def2_clean:
            # 比较节点
            nodes1 = {n.get("id"): n for n in def1_clean.get("nodes", [])}
            nodes2 = {n.get("id"): n for n in def2_clean.get("nodes", [])}
            
            node_changes = []
            
            # 新增的节点
            for node_id in nodes2:
                if node_id not in nodes1:
                    node_changes.append({
                        "type": "added",
                        "node": nodes2[node_id]
                    })
            
            # 删除的节点
            for node_id in nodes1:
                if node_id not in nodes2:
                    node_changes.append({
                        "type": "removed",
                        "node": nodes1[node_id]
                    })
            
            # 修改的节点
            for node_id in nodes1:
                if node_id in nodes2 and nodes1[node_id] != nodes2[node_id]:
                    node_changes.append({
                        "type": "modified",
                        "node_id": node_id,
                        "old": nodes1[node_id],
                        "new": nodes2[node_id]
                    })
            
            # 比较边
            edges1 = {(e.get("source"), e.get("target")): e for e in def1_clean.get("edges", [])}
            edges2 = {(e.get("source"), e.get("target")): e for e in def2_clean.get("edges", [])}
            
            edge_changes = []
            
            # 新增的边
            for edge_key in edges2:
                if edge_key not in edges1:
                    edge_changes.append({
                        "type": "added",
                        "edge": edges2[edge_key]
                    })
            
            # 删除的边
            for edge_key in edges1:
                if edge_key not in edges2:
                    edge_changes.append({
                        "type": "removed",
                        "edge": edges1[edge_key]
                    })
            
            if node_changes or edge_changes:
                differences["changes"].append({
                    "field": "definition",
                    "type": "modified",
                    "node_changes": node_changes,
                    "edge_changes": edge_changes
                })
        
        # 比较变量
        vars1 = w1.variables or []
        vars2 = w2.variables or []
        if vars1 != vars2:
            differences["changes"].append({
                "field": "variables",
                "type": "modified",
                "old": vars1,
                "new": vars2
            })
        
        # 比较触发器
        triggers1 = w1.triggers or []
        triggers2 = w2.triggers or []
        if triggers1 != triggers2:
            differences["changes"].append({
                "field": "triggers",
                "type": "modified",
                "old": triggers1,
                "new": triggers2
            })
        
        # 比较标签
        tags1 = set(w1.tags or [])
        tags2 = set(w2.tags or [])
        if tags1 != tags2:
            added_tags = list(tags2 - tags1)
            removed_tags = list(tags1 - tags2)
            differences["changes"].append({
                "field": "tags",
                "type": "modified",
                "added": added_tags,
                "removed": removed_tags
            })
        
        # 生成文本差异
        def1_json = json.dumps(def1_clean, indent=2, ensure_ascii=False, sort_keys=True)
        def2_json = json.dumps(def2_clean, indent=2, ensure_ascii=False, sort_keys=True)
        
        diff_lines = list(difflib.unified_diff(
            def1_json.splitlines(keepends=True),
            def2_json.splitlines(keepends=True),
            fromfile=f"version {version1}",
            tofile=f"version {version2}"
        ))
        
        differences["diff_text"] = "".join(diff_lines)
        differences["summary"] = {
            "total_changes": len(differences["changes"]),
            "nodes_added": len([c for c in node_changes if c["type"] == "added"]),
            "nodes_removed": len([c for c in node_changes if c["type"] == "removed"]),
            "nodes_modified": len([c for c in node_changes if c["type"] == "modified"]),
            "edges_added": len([c for c in edge_changes if c["type"] == "added"]),
            "edges_removed": len([c for c in edge_changes if c["type"] == "removed"])
        }
        
        return differences


class ApprovalTaskService:
    """审批任务服务"""
    
    @staticmethod
    def create_task(
        db: Session,
        execution_id: UUID,
        node_id: str,
        node_name: str,
        assignee_type: str,
        assignee_id: UUID,
        timeout_seconds: int = 86400,
        auto_action: str = "reject",
        input_data: Dict[str, Any] = None
    ):
        """创建审批任务"""
        from datetime import timedelta
        from app.models.workflow import ApprovalTask
        
        task = ApprovalTask(
            execution_id=execution_id,
            node_id=node_id,
            node_name=node_name,
            assignee_type=assignee_type,
            assignee_id=assignee_id,
            timeout_seconds=timeout_seconds,
            auto_action=auto_action,
            timeout_at=datetime.utcnow() + timedelta(seconds=timeout_seconds),
            input_data=input_data or {},
            status="pending"
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    
    @staticmethod
    def get_task_by_id(db: Session, task_id: UUID):
        """根据ID获取审批任务"""
        from app.models.workflow import ApprovalTask
        return db.query(ApprovalTask).filter(ApprovalTask.id == task_id).first()
    
    @staticmethod
    def get_task_by_execution_and_node(db: Session, execution_id: UUID, node_id: str):
        """根据执行ID和节点ID获取审批任务"""
        from app.models.workflow import ApprovalTask
        return db.query(ApprovalTask).filter(
            ApprovalTask.execution_id == execution_id,
            ApprovalTask.node_id == node_id
        ).first()
    
    @staticmethod
    def list_pending_tasks(
        db: Session,
        user_id: UUID = None,
        role_ids: List[UUID] = None,
        department_id: UUID = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List, int]:
        """获取待审批任务列表
        
        根据用户ID、角色ID列表和部门ID查询用户有权审批的任务
        """
        from app.models.workflow import ApprovalTask, WorkflowExecution, Workflow
        
        query = db.query(ApprovalTask).filter(ApprovalTask.status == "pending")
        
        # 构建查询条件
        if user_id or role_ids or department_id:
            conditions = []
            if user_id:
                conditions.append(
                    (ApprovalTask.assignee_type == "user") & (ApprovalTask.assignee_id == user_id)
                )
            if role_ids:
                conditions.append(
                    (ApprovalTask.assignee_type == "role") & (ApprovalTask.assignee_id.in_(role_ids))
                )
            if department_id:
                conditions.append(
                    (ApprovalTask.assignee_type == "department") & (ApprovalTask.assignee_id == department_id)
                )
            
            if conditions:
                from sqlalchemy import or_
                query = query.filter(or_(*conditions))
        
        total = query.count()
        tasks = query.order_by(ApprovalTask.created_at.desc()).offset(skip).limit(limit).all()
        return tasks, total
    
    @staticmethod
    def list_user_tasks(
        db: Session,
        user_id: UUID,
        status: str = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List, int]:
        """获取用户的审批任务列表（已审批的）"""
        from app.models.workflow import ApprovalTask
        
        query = db.query(ApprovalTask).filter(ApprovalTask.completed_by == user_id)
        
        if status:
            query = query.filter(ApprovalTask.status == status)
        else:
            # 默认查询已完成的（非pending）
            query = query.filter(ApprovalTask.status != "pending")
        
        total = query.count()
        tasks = query.order_by(ApprovalTask.completed_at.desc()).offset(skip).limit(limit).all()
        return tasks, total
    
    @staticmethod
    def approve_task(
        db: Session,
        task_id: UUID,
        user_id: UUID,
        comment: str = None
    ):
        """审批通过"""
        from app.models.workflow import ApprovalTask
        
        task = ApprovalTaskService.get_task_by_id(db, task_id)
        if not task:
            raise ValueError("审批任务不存在")
        
        if task.status != "pending":
            raise ValueError(f"审批任务状态不正确，当前状态: {task.status}")
        
        task.status = "approved"
        task.completed_by = user_id
        task.completed_at = datetime.utcnow()
        task.comment = comment
        task.output_data = {
            "action": "approved",
            "comment": comment,
            "approved_by": str(user_id),
            "approved_at": task.completed_at.isoformat()
        }
        
        db.commit()
        db.refresh(task)
        return task
    
    @staticmethod
    def reject_task(
        db: Session,
        task_id: UUID,
        user_id: UUID,
        comment: str = None
    ):
        """审批拒绝"""
        from app.models.workflow import ApprovalTask
        
        task = ApprovalTaskService.get_task_by_id(db, task_id)
        if not task:
            raise ValueError("审批任务不存在")
        
        if task.status != "pending":
            raise ValueError(f"审批任务状态不正确，当前状态: {task.status}")
        
        task.status = "rejected"
        task.completed_by = user_id
        task.completed_at = datetime.utcnow()
        task.comment = comment
        task.output_data = {
            "action": "rejected",
            "comment": comment,
            "rejected_by": str(user_id),
            "rejected_at": task.completed_at.isoformat()
        }
        
        db.commit()
        db.refresh(task)
        return task
    
    @staticmethod
    def transfer_task(
        db: Session,
        task_id: UUID,
        user_id: UUID,
        new_assignee_id: UUID,
        comment: str = None
    ):
        """转办审批任务"""
        from app.models.workflow import ApprovalTask
        
        task = ApprovalTaskService.get_task_by_id(db, task_id)
        if not task:
            raise ValueError("审批任务不存在")
        
        if task.status != "pending":
            raise ValueError(f"审批任务状态不正确，当前状态: {task.status}")
        
        # 保存原指派人信息
        task.transferred_from = user_id
        task.transferred_at = datetime.utcnow()
        
        # 更新指派人
        task.assignee_type = "user"  # 转办后通常指定为具体用户
        task.assignee_id = new_assignee_id
        task.status = "transferred"
        task.comment = comment
        task.output_data = {
            "action": "transferred",
            "comment": comment,
            "transferred_by": str(user_id),
            "transferred_at": task.transferred_at.isoformat(),
            "new_assignee_id": str(new_assignee_id)
        }
        
        db.commit()
        db.refresh(task)
        return task
    
    @staticmethod
    def check_user_can_approve(db: Session, task_id: UUID, user_id: UUID, role_ids: List[UUID] = None, department_id: UUID = None) -> bool:
        """检查用户是否有权限审批该任务"""
        from app.models.workflow import ApprovalTask
        
        task = ApprovalTaskService.get_task_by_id(db, task_id)
        if not task or task.status != "pending":
            return False
        
        # 检查是否是直接指派人
        if task.assignee_type == "user" and task.assignee_id == user_id:
            return True
        
        # 检查是否是指定角色的成员
        if task.assignee_type == "role" and role_ids and task.assignee_id in role_ids:
            return True
        
        # 检查是否是指定部门的成员
        if task.assignee_type == "department" and department_id and task.assignee_id == department_id:
            return True
        
        return False
