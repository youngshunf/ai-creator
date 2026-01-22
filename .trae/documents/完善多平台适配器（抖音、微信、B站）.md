我将参考 `xiaohongshu.py` 的实现，为抖音、微信公众号完善适配器，并新增 Bilibili 适配器。所有适配器将优先尝试使用 Playwright 进行自动化操作，如果失败则通过返回错误信息触发上层的 `browser-use` 降级机制（基于基类的 `get_publish_prompt`）。

### 1. 新增 Bilibili 适配器 (`bilibili.py`)

- **文件路径**: `apps/sidecar/src/sidecar/platforms/bilibili.py`
- **功能实现**:
  - `spec`: 定义视频投稿规范（标题长度、简介长度、标签数量等）。
  - `check_login_status`: 通过检查 `SESSDATA` Cookie 或访问创作中心主页来验证登录。
  - `get_user_profile`: 访问 `https://member.bilibili.com/platform/home` 提取昵称、头像、粉丝数等数据。
  - `publish`: 实现视频投稿流程（上传视频 -> 填写信息 -> 上传封面 -> 提交）。

### 2. 完善抖音适配器 (`douyin.py`)

- **文件路径**: `apps/sidecar/src/sidecar/platforms/douyin.py`
- **功能实现**:
  - **新增** `publish`: 实现视频发布流程。
    - 导航至 `https://creator.douyin.com/creator-micro/content/upload`。
    - 处理视频上传、标题/描述填写、话题标签选择、封面设置及发布确认。

### 3. 完善微信公众号适配器 (`wechat.py`)

- **文件路径**: `apps/sidecar/src/sidecar/platforms/wechat.py`
- **功能实现**:
  - **新增** `check_login_status`: 通过 Cookie 或页面元素检测登录状态。
  - **新增** `get_user_profile`: 从公众号后台首页提取账号信息。
  - **新增** `publish`: 实现图文消息发布流程（新建图文 -> 编辑内容 -> 保存草稿/群发）。由于微信编辑器较为复杂，将重点实现基础文本和图片的插入。

### 4. 注册新平台

- **文件路径**: `apps/sidecar/src/sidecar/platforms/__init__.py`
- **操作**: 导出 `BilibiliAdapter`，确保系统能识别新平台。

### 降级策略说明

- 所有 `publish` 方法将包含 `try-catch` 块。
- 若 Playwright 自动化过程中出现元素未找到或超时等错误，将返回 `PublishResult(success=False, error_message="...")`。
- 这将允许上层逻辑捕获失败并利用 `get_publish_prompt` 生成提示词，转交给 `browser-use` 进行 AI 驱动的操作。
