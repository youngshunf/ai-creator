"""
Agent Core 测试配置

@author Ysf
@date 2025-12-28
"""

import pytest


@pytest.fixture
def sample_publish_content():
    """示例发布内容"""
    from agent_core.platforms import PublishContent
    return PublishContent(
        title="测试标题",
        content="这是测试内容",
        images=["image1.jpg", "image2.jpg"],
        hashtags=["测试", "AI"],
    )
