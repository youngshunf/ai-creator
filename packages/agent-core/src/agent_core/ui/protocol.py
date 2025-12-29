"""
UI 协议定义 - Agent 与前端之间的 UI 通讯协议
@author Ysf

基于 A2UI (Agent to UI) 思想，定义声明式 UI 组件结构。
Agent 输出 JSON，前端渲染为原生组件。
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class UIComponentType(str, Enum):
    """支持的 UI 组件类型"""
    
    # 布局组件
    CARD = "card"
    ROW = "row"
    COLUMN = "column"
    
    # 文本组件
    TEXT = "text"
    MARKDOWN = "markdown"
    HEADING = "heading"
    
    # 表单组件
    FORM = "form"
    INPUT = "input"
    TEXTAREA = "textarea"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    BUTTON = "button"
    
    # 数据展示
    TABLE = "table"
    LIST = "list"
    IMAGE = "image"
    
    # 特殊
    DIVIDER = "divider"
    PROGRESS = "progress"


class UIEvent(BaseModel):
    """UI 事件定义"""
    
    # 事件类型 (点击、变更、提交等)
    type: str = Field(..., description="事件类型: onClick, onChange, onSubmit")
    
    # 动作标识 (用于回传给 Agent)
    action_id: str = Field(..., description="动作 ID，Agent 用于识别用户操作")
    
    # 可选的附加数据
    payload: Optional[Dict[str, Any]] = Field(default=None, description="附加数据")


class UIComponent(BaseModel):
    """
    UI 组件定义
    
    采用树形结构，支持嵌套组件。
    """
    
    # 组件类型
    type: UIComponentType = Field(..., description="组件类型")
    
    # 组件 ID (用于表单数据绑定)
    id: Optional[str] = Field(default=None, description="组件 ID")
    
    # 组件属性 (不同类型的组件有不同的属性)
    props: Dict[str, Any] = Field(default_factory=dict, description="组件属性")
    
    # 子组件 (用于布局组件)
    children: Optional[List["UIComponent"]] = Field(default=None, description="子组件")
    
    # 事件绑定
    events: Optional[Dict[str, UIEvent]] = Field(default=None, description="事件绑定")

    class Config:
        use_enum_values = True


class UIMessage(BaseModel):
    """
    UI 消息
    
    Agent 发送给前端的完整 UI 渲染指令。
    """
    
    # 根组件
    ui: UIComponent = Field(..., description="根 UI 组件")
    
    # 是否期待用户响应 (如表单提交)
    expects_response: bool = Field(
        default=False, 
        description="是否等待用户交互后再继续"
    )
    
    # 超时时间 (秒)，仅当 expects_response=True 时有效
    timeout_seconds: Optional[int] = Field(
        default=None, 
        description="等待用户响应的超时时间"
    )
    
    # 可选的消息 ID
    message_id: Optional[str] = Field(default=None, description="消息 ID")


class UIResponse(BaseModel):
    """
    用户 UI 交互响应
    
    前端发送给 Agent 的用户操作结果。
    """
    
    # 对应的 UI 消息 ID
    message_id: Optional[str] = Field(default=None, description="原始消息 ID")
    
    # 触发的动作 ID
    action_id: str = Field(..., description="触发的动作 ID")
    
    # 表单数据 (如果是表单提交)
    form_data: Optional[Dict[str, Any]] = Field(default=None, description="表单数据")
    
    # 其他事件数据
    event_data: Optional[Dict[str, Any]] = Field(default=None, description="事件数据")


# 更新递归引用
UIComponent.model_rebuild()
