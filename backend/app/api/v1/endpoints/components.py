from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.core.security import get_current_user, get_current_superuser
from app.services.component_service import ComponentService, ComponentCategoryService
from app.schemas.component import (
    ComponentCreate, ComponentUpdate, ComponentResponse, ComponentListResponse,
    ComponentCategoryCreate, ComponentCategoryResponse,
    ComponentTestRequest, ComponentTestResponse,
)
from app.schemas.user import PaginatedResponse
from typing import List, Any
from app.models.user import User

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
def list_components(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    component_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取组件列表"""
    skip = (page - 1) * page_size
    components, total = ComponentService.list_components(
        db,
        skip=skip,
        limit=page_size,
        search=search,
        component_type=component_type,
        status=status
    )
    
    # 将SQLAlchemy对象转换为Pydantic模型
    component_list = [ComponentListResponse.model_validate(c).model_dump() for c in components]
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "data": component_list
    }


@router.post("", response_model=ComponentResponse, status_code=status.HTTP_201_CREATED)
def create_component(
    component_data: ComponentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建组件"""
    try:
        component = ComponentService.create_component(db, component_data, current_user.id)
        return component
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{component_id}", response_model=ComponentResponse)
def get_component(
    component_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取组件详情"""
    component = ComponentService.get_by_id(db, component_id)
    if not component:
        raise HTTPException(status_code=404, detail="组件不存在")
    return component


@router.put("/{component_id}", response_model=ComponentResponse)
def update_component(
    component_id: UUID,
    component_data: ComponentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新组件"""
    component = ComponentService.get_by_id(db, component_id)
    if not component:
        raise HTTPException(status_code=404, detail="组件不存在")
    
    # 检查权限
    if component.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权修改此组件")
    
    return ComponentService.update_component(db, component, component_data)


@router.delete("/{component_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_component(
    component_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除组件"""
    component = ComponentService.get_by_id(db, component_id)
    if not component:
        raise HTTPException(status_code=404, detail="组件不存在")
    
    # 检查权限
    if component.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权删除此组件")
    
    ComponentService.delete_component(db, component)
    return None


@router.post("/{component_id}/test")
async def test_component(
    component_id: UUID,
    test_data: ComponentTestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """测试组件"""
    component = ComponentService.get_by_id(db, component_id)
    if not component:
        raise HTTPException(status_code=404, detail="组件不存在")
    
    result = await ComponentService.test_component(db, component, test_data)
    return result


@router.post("/{component_id}/publish", response_model=ComponentResponse)
def publish_component(
    component_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发布组件"""
    component = ComponentService.get_by_id(db, component_id)
    if not component:
        raise HTTPException(status_code=404, detail="组件不存在")
    
    # 检查权限
    if component.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权发布此组件")
    
    return ComponentService.publish_component(db, component)


# ============ 组件分类 ============

@router.get("/categories/tree")
def get_category_tree(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取组件分类树"""
    categories = ComponentCategoryService.get_categories(db)
    return categories


@router.post("/categories", response_model=ComponentCategoryResponse)
def create_category(
    category_data: ComponentCategoryCreate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """创建组件分类（仅管理员）"""
    category = ComponentCategoryService.create_category(
        db,
        name=category_data.name,
        code=category_data.code,
        description=category_data.description,
        icon=category_data.icon,
        category_type=category_data.category_type
    )
    return category
