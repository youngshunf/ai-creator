# Graph 定义规范

**@author Ysf**
**版本**: 1.0.0
**创建日期**: 2025-12-27

## 概述

Graph 是 AI Creator 中用于定义 AI 工作流的声明式配置文件，采用 YAML 或 JSON 格式。每个 Graph 描述了一个完整的 Agent 执行流程，包括输入参数、状态管理、节点执行、边连接和输出定义。

## 设计目标

1. **声明式**: 通过配置而非代码定义工作流
2. **端云对等**: 同一 Graph 可在本地 (Sidecar) 和云端 (Backend) 无差异执行
3. **类型安全**: 强类型定义，编译时验证
4. **表达式系统**: 灵活的变量引用和数据转换
5. **可组合**: 支持 Graph 嵌套和工具复用

## 文件格式

### 基本结构

```yaml
apiVersion: agent/v1
kind: Graph
metadata:
  name: <graph-name>
  version: <semantic-version>
  description: <description>
  author: <author-name>
  tags: [<tag1>, <tag2>]
spec:
  inputs: <inputs-definition>
  state: <state-definition>
  nodes: <nodes-list>
  edges: <edges-list>
  outputs: <outputs-definition>
```

### 字段说明

#### apiVersion (必填)
- 类型: `string`
- 格式: `agent/v1`
- 说明: API 版本，用于向后兼容

#### kind (必填)
- 类型: `string`
- 固定值: `Graph`
- 说明: 资源类型标识

#### metadata (必填)
- 类型: `object`
- 说明: Graph 元数据

**metadata 字段**:
```yaml
metadata:
  name: content-creation           # 必填，Graph 唯一标识
  version: "1.0.0"                 # 必填，语义化版本
  description: "内容创作工作流"     # 可选，描述信息
  author: "Ysf"                    # 可选，作者
  tags: ["content", "creation"]    # 可选，标签
```

#### spec (必填)
- 类型: `object`
- 说明: Graph 核心规格定义

---

## spec.inputs - 输入参数定义

定义 Graph 执行时需要的外部输入参数。

### 格式

```yaml
spec:
  inputs:
    <param-name>:
      type: <type>
      required: <boolean>
      default: <default-value>
      description: <description>
```

### 字段说明

- **param-name**: 参数名称（字母、数字、下划线）
- **type**: 数据类型，支持：
  - `string`: 字符串
  - `integer`: 整数
  - `float`: 浮点数
  - `boolean`: 布尔值
  - `object`: 对象
  - `array`: 数组
- **required**: 是否必填（默认 `false`）
- **default**: 默认值（可选）
- **description**: 参数描述（可选）

### 示例

```yaml
spec:
  inputs:
    topic:
      type: string
      required: true
      description: "文章主题"

    style:
      type: string
      required: false
      default: "professional"
      description: "写作风格"

    max_length:
      type: integer
      required: false
      default: 2000
      description: "最大字数"
```

---

## spec.state - 状态定义

定义 Graph 执行过程中的中间状态变量。

### 格式

```yaml
spec:
  state:
    <state-name>:
      type: <type>
      default: <default-value>
      description: <description>
```

### 字段说明

- **state-name**: 状态变量名称
- **type**: 数据类型（同 inputs）
- **default**: 初始值（可选）
- **description**: 变量描述（可选）

### 示例

```yaml
spec:
  state:
    outline:
      type: string
      description: "文章大纲"

    content:
      type: string
      description: "文章正文"

    images:
      type: array
      default: []
      description: "配图列表"
```

---

## spec.nodes - 节点定义

定义 Graph 中的执行节点，每个节点代表一次工具调用。

### 格式

```yaml
spec:
  nodes:
    - name: <node-name>
      tool: <tool-name>
      params: <params-object>
      outputs: <outputs-mapping>
      condition: <condition-expression>
```

### 字段说明

- **name** (必填): 节点唯一标识
- **tool** (必填): 使用的工具名称（需在 ToolRegistry 中注册）
- **params** (可选): 传递给工具的参数（支持表达式）
- **outputs** (可选): 输出映射，将工具返回值写入 state
- **condition** (可选): 节点执行条件（布尔表达式）

### 示例

```yaml
spec:
  nodes:
    # 节点1: 生成大纲
    - name: generate_outline
      tool: llm_generate
      params:
        prompt: "为主题「${inputs.topic}」生成文章大纲"
        model: "${runtime.model_fast}"
        max_tokens: 1000
      outputs:
        outline: "$.content"

    # 节点2: 生成正文
    - name: generate_content
      tool: llm_generate
      params:
        prompt: |
          基于以下大纲撰写文章：
          ${state.outline}

          要求风格：${inputs.style}
          最大字数：${inputs.max_length}
        model: "${runtime.model_default}"
        max_tokens: 4000
      outputs:
        content: "$.content"

    # 节点3: 生成配图（条件执行）
    - name: generate_images
      tool: image_generate
      condition: "${inputs.include_images == true}"
      params:
        prompts: "${state.image_prompts}"
      outputs:
        images: "$[*].url"
```

---

## spec.edges - 边定义

定义节点之间的连接关系和执行顺序。

### 格式

```yaml
spec:
  edges:
    - from: <source-node>
      to: <target-node>
      condition: <condition-expression>
```

### 字段说明

- **from** (必填): 源节点名称（`START` 表示起始）
- **to** (必填): 目标节点名称（`END` 表示结束）
- **condition** (可选): 条件表达式（默认无条件跳转）

### 特殊节点

- **START**: 虚拟起始节点
- **END**: 虚拟结束节点

### 示例

```yaml
spec:
  edges:
    # 从 START 到第一个节点
    - from: START
      to: generate_outline

    # 无条件跳转
    - from: generate_outline
      to: generate_content

    # 条件跳转
    - from: generate_content
      to: generate_images
      condition: "${inputs.include_images == true}"

    - from: generate_content
      to: END
      condition: "${inputs.include_images == false}"

    - from: generate_images
      to: END
```

---

## spec.outputs - 输出定义

定义 Graph 执行完成后的输出结果。

### 格式

```yaml
spec:
  outputs:
    <output-name>: <expression>
```

### 示例

```yaml
spec:
  outputs:
    final_content: "${state.content}"
    outline: "${state.outline}"
    images: "${state.images}"
    metadata:
      topic: "${inputs.topic}"
      style: "${inputs.style}"
      length: "${len(state.content)}"
```

---

## 表达式系统

Graph 支持灵活的表达式系统，用于动态引用变量和计算值。

### 表达式语法

表达式使用 `${...}` 包裹，内部支持：

1. **变量引用**:
   - `${inputs.xxx}`: 引用输入参数
   - `${state.xxx}`: 引用状态变量
   - `${runtime.xxx}`: 引用运行时上下文

2. **JSON Path** (用于 outputs 映射):
   - `$.field`: 提取对象字段
   - `$[0]`: 提取数组元素
   - `$[*].field`: 提取所有元素的字段

3. **运算符**:
   - 比较: `==`, `!=`, `>`, `<`, `>=`, `<=`
   - 逻辑: `and`, `or`, `not`
   - 算术: `+`, `-`, `*`, `/`, `%`

4. **函数**:
   - `len(x)`: 获取长度
   - `str(x)`: 转字符串
   - `int(x)`: 转整数

### runtime 上下文

`runtime` 对象包含运行时信息：

```python
runtime.user_id          # 用户 ID
runtime.runtime_type     # 运行环境 (LOCAL/CLOUD)
runtime.model_default    # 默认模型
runtime.model_fast       # 快速模型
runtime.trace_id         # 追踪 ID
runtime.run_id           # 运行 ID
```

### 表达式示例

```yaml
# 字符串插值
prompt: "为主题「${inputs.topic}」生成大纲"

# 条件判断
condition: "${state.word_count > inputs.max_length}"

# 运算
max_tokens: "${inputs.max_length * 2}"

# JSON Path 提取
outputs:
  outline: "$.content"           # 提取 content 字段
  images: "$[*].url"             # 提取所有元素的 url 字段
  first_image: "$[0].url"        # 提取第一个元素的 url
```

---

## 完整示例

### 示例1: 内容创作工作流

```yaml
apiVersion: agent/v1
kind: Graph
metadata:
  name: content-creation
  version: "1.0.0"
  description: "AI 内容创作工作流"
  author: "Ysf"
  tags: ["content", "creation", "ai"]

spec:
  # 输入参数
  inputs:
    topic:
      type: string
      required: true
      description: "文章主题"

    style:
      type: string
      required: false
      default: "professional"
      description: "写作风格"

    include_images:
      type: boolean
      required: false
      default: false
      description: "是否生成配图"

  # 状态变量
  state:
    outline:
      type: string
      description: "文章大纲"

    content:
      type: string
      description: "文章正文"

    images:
      type: array
      default: []
      description: "配图 URL 列表"

  # 节点定义
  nodes:
    - name: generate_outline
      tool: llm_generate
      params:
        prompt: "为主题「${inputs.topic}」生成文章大纲，风格：${inputs.style}"
        model: "${runtime.model_fast}"
        max_tokens: 1000
      outputs:
        outline: "$.content"

    - name: generate_content
      tool: llm_generate
      params:
        prompt: |
          基于以下大纲撰写文章：
          ${state.outline}
        model: "${runtime.model_default}"
        max_tokens: 4000
      outputs:
        content: "$.content"

    - name: generate_images
      tool: image_generate
      condition: "${inputs.include_images == true}"
      params:
        count: 3
        style: "realistic"
      outputs:
        images: "$[*].url"

  # 边定义
  edges:
    - from: START
      to: generate_outline

    - from: generate_outline
      to: generate_content

    - from: generate_content
      to: generate_images
      condition: "${inputs.include_images == true}"

    - from: generate_content
      to: END
      condition: "${inputs.include_images == false}"

    - from: generate_images
      to: END

  # 输出定义
  outputs:
    final_content: "${state.content}"
    outline: "${state.outline}"
    images: "${state.images}"
    metadata:
      topic: "${inputs.topic}"
      style: "${inputs.style}"
```

### 示例2: 热点分析工作流

```yaml
apiVersion: agent/v1
kind: Graph
metadata:
  name: viral-analysis
  version: "1.0.0"
  description: "热点趋势分析工作流"
  author: "Ysf"

spec:
  inputs:
    platform:
      type: string
      required: true
      description: "平台名称"

    category:
      type: string
      required: false
      description: "内容类别"

  state:
    hot_topics:
      type: array
      description: "热点话题列表"

    analysis_result:
      type: object
      description: "分析结果"

  nodes:
    - name: fetch_hot_topics
      tool: bettafish_analyzer
      params:
        platform: "${inputs.platform}"
        category: "${inputs.category}"
        limit: 20
      outputs:
        hot_topics: "$.topics"

    - name: analyze_trends
      tool: llm_generate
      params:
        prompt: |
          分析以下热点话题的趋势：
          ${state.hot_topics}

          给出：
          1. 核心趋势总结
          2. 内容创作建议
          3. 潜在爆款方向
        model: "${runtime.model_default}"
        max_tokens: 2000
      outputs:
        analysis_result: "$.content"

  edges:
    - from: START
      to: fetch_hot_topics

    - from: fetch_hot_topics
      to: analyze_trends

    - from: analyze_trends
      to: END

  outputs:
    hot_topics: "${state.hot_topics}"
    analysis: "${state.analysis_result}"
```

---

## 验证规则

GraphValidator 会执行以下验证：

### 1. Schema 验证
- ✅ 必填字段存在：`apiVersion`, `kind`, `metadata.name`, `spec`
- ✅ `apiVersion` 格式正确：`agent/v1`
- ✅ `kind` 值为 `Graph`
- ✅ `metadata.version` 符合语义化版本格式

### 2. 类型验证
- ✅ `inputs` 和 `state` 的 `type` 合法
- ✅ `required` 为布尔值
- ✅ `default` 类型与声明的 `type` 匹配

### 3. 引用验证
- ✅ `nodes[].tool` 在 ToolRegistry 中注册
- ✅ `edges[].from` 和 `edges[].to` 引用的节点存在
- ✅ 表达式中的变量引用合法

### 4. 图结构验证
- ✅ 图连通：从 START 可达所有节点，所有节点可达 END
- ✅ 无孤立节点
- ✅ 无死循环（拓扑排序检测）

### 5. 表达式验证
- ✅ `${...}` 语法正确
- ✅ 引用的字段存在（`inputs.xxx`, `state.xxx`, `runtime.xxx`）
- ✅ JSON Path 语法正确

---

## 最佳实践

### 1. 命名规范
- Graph 名称：小写字母 + 连字符（`content-creation`）
- 节点名称：动词 + 名词（`generate_outline`）
- 状态变量：名词（`outline`, `content`）

### 2. 模块化
- 将复杂工作流拆分为多个小 Graph
- 使用通用工具，避免重复实现

### 3. 错误处理
- 为关键节点添加 `condition` 检查
- 使用默认值避免空值错误

### 4. 性能优化
- 使用 `runtime.model_fast` 处理简单任务
- 合理设置 `max_tokens` 避免浪费

### 5. 文档化
- 添加详细的 `description`
- 为复杂表达式添加注释

---

## 扩展方向

未来版本可能支持：

1. **子 Graph 调用**: 在 Graph 中嵌套调用其他 Graph
2. **并行执行**: 支持节点并行执行
3. **循环结构**: 支持 while/for 循环
4. **异常处理**: 支持 try-catch 机制
5. **版本管理**: 支持多版本 Graph 共存

---

## 参考文档

- [系统架构](./01-系统架构.md)
- [Agent Runtime](./05-Agent-Runtime.md)
- [开发规范](./11-开发规范.md)
