# Agent Definition Specification (v1)

为了使 **Meta-Agent** (智能工作流生成器) 能够通过语义检索 (RAG) 准确地发现并复用现有的 Agent，所有 Agent 定义文件 (`.yaml`) 必须严格遵循以下规范。

## 1. 核心原则

**"Description is API"** —— 对于 Meta-Agent 来说，`metadata.description` 和 `inputs` 的描述就是它理解该 Agent 能力的唯一途径。

*   ❌ 坏的描述: "分析博主" (太模糊，Meta-Agent 不知道包含什么分析维度)
*   ✅ 好的描述: "深度分析小红书/抖音博主的个人主页。爬取最近 10 篇笔记，分析其内容风格、受众画像、高频关键词，并评估其与'科技数码'领域的匹配度。"

## 2. YAML 结构规范

```yaml
apiVersion: agent/v1
kind: Graph
metadata:
  # [必填] 唯一标识符，建议使用 动词-名词 结构
  name: profile-analysis-expert
  
  # [必填] 语义化版本
  version: "1.0.0"
  
  # [必填] 详细的能力描述。这是 Meta-Agent 进行 RAG 检索的核心依据。
  # 请详细描述：
  # 1. 它可以做什么 (Capabilities)
  # 2. 它的输入是什么 (Inputs)
  # 3. 它的输出包含什么 (Outputs)
  # 4. 它的适用场景 (Use Cases)
  description: >
    这是一个专家级的社交媒体博主分析智能体。
    
    核心能力：
    1. 多平台支持：支持小红书、抖音、Bilibili 博主主页分析。
    2. 深度内容分析：读取历史作品，提取风格标签（如"幽默"、"硬核"）。
    3. 商业价值评估：预估其广告报价范围和粉丝粘性。
    
    适用场景：
    - 寻找合适的 KOL 进行投放。
    - 竞品账号分析。
    
  # [必填] 标签，用于粗粒度过滤
  tags: ["analysis", "social-media", "profile", "expert"]
  
  # [可选] 作者信息
  author: "CreatorFlow Team"

spec:
  # [必填] 输入定义
  # Meta-Agent 会根据这里的 schema 自动生成调用代码
  inputs:
    profile_url:
      type: string
      description: "目标博主的主页链接 (HTTPS)"
      required: true
      example: "https://www.xiaohongshu.com/user/profile/xxx"
      
    analysis_depth:
      type: string
      description: "分析深度模式"
      default: "standard"
      enum: ["quick", "standard", "deep"]
      
    focus_keywords:
      type: array
      description: "关注的关键词列表，分析时会着重检查博主是否提及这些词"
      default: []

  # [必填] 输出定义
  # 明确告诉 Meta-Agent 调用后能拿到什么数据
  outputs:
    report_markdown:
      type: string
      description: "格式化后的分析报告 (Markdown)"
      
    match_score:
      type: integer
      description: "匹配度打分 (0-100)"
      
    audience_tags:
      type: array
      description: "受众标签列表"

  # (State, Nodes, Edges 保持原有规范)
  state: ...
  nodes: ...
  edges: ...
```

## 3. 规范检查清单

在提交一个新的 Agent 定义前，请自查：

1.  **名称是否唯一且达意？** 避免使用 `test-agent`, `demo` 等无意义名称。
2.  **描述是否包含"关键词"？** 如果用户搜 "KOL 评估"，你的描述里包含 "KOL" 或 "评估" 吗？
3.  **输入参数是否有默认值？** 为了方便 Meta-Agent 调用，非核心参数尽量提供默认值。
4.  **输入描述是否清晰？** 如果需要特定格式（如 URL），请在 description 或 example 中注明。
5.  **输出是否明确？** Meta-Agent 需要知道能不能从你的 Agent 拿到结果传给下一个节点。

## 4. 示例：如何让 Meta-Agent "看懂"

### 场景：用户说 "帮我找几个合适的博主发广告"

Meta-Agent 会在向量数据库中搜索 "找博主", "广告", "发广告"。

如果你的 YAML 如下定义：

```yaml
metadata:
  name: search-tool
  description: "搜素工具" # ❌ 极差。Meta-Agent 无法匹配到"博主"或"广告"。
```

Meta-Agent 将**忽略**此 Agent。

如果定义如下：

```yaml
metadata:
  name: influencer-discovery-agent
  description: "用于广告投放的博主发现与筛选智能体。可以根据产品类型搜索匹配的 KOL/KOC，并根据粉丝量、互动率进行过滤。" # ✅ 优秀
  tags: ["search", "influencer", "ads"]
```

Meta-Agent 将**高置信度**地选中此 Agent，并将其加入工作流。
