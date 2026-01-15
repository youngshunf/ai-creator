"""
Pydantic Schemas for Stagehand structured extraction

用于 Stagehand extract() API 的结构化数据模型。

@author Ysf
@date 2026-01-10
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """用户资料 - 从平台页面提取"""
    nickname: str = Field(..., description="用户昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    followers: Optional[int] = Field(None, description="粉丝数")
    following: Optional[int] = Field(None, description="关注数")
    user_id: Optional[str] = Field(None, description="用户ID")
    bio: Optional[str] = Field(None, description="个人简介")


class LoginStatus(BaseModel):
    """登录状态"""
    is_logged_in: bool = Field(..., description="是否已登录")
    username: Optional[str] = Field(None, description="用户名")
    error_message: Optional[str] = Field(None, description="错误信息")


class PublishResult(BaseModel):
    """发布结果"""
    success: bool = Field(..., description="是否发布成功")
    post_url: Optional[str] = Field(None, description="发布后的链接")
    post_id: Optional[str] = Field(None, description="作品ID")
    error_message: Optional[str] = Field(None, description="错误信息")


class PageAction(BaseModel):
    """页面操作"""
    action_type: str = Field(..., description="操作类型: click, input, scroll, etc.")
    selector: Optional[str] = Field(None, description="元素选择器")
    description: str = Field(..., description="操作描述")
