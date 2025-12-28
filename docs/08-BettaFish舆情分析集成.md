# BettaFish 舆情分析系统集成方案

> 让 AI Agent 拥有"嗅觉" - 从热点追踪到爆款创作 | 版本: v1.0 | 更新: 2025-12-25

---

## 1. BettaFish 项目概述

### 1.1 项目定位

**BettaFish (微舆)** 是一个 AI 驱动的多智能体舆情分析系统，用于监控 30+ 主流社交媒体平台的公众情绪，结合网络爬虫、多模态 AI 分析和智能报告生成，从海量评论数据中提取洞察。

### 1.2 核心能力矩阵

| 能力维度 | 描述 | 对创作的价值 |
|---------|------|-------------|
| **热点发现** | 实时监控 30+ 平台热门话题 | 第一时间捕捉爆款选题 |
| **情绪分析** | 22 语言情感倾向识别 | 把握用户情绪痛点 |
| **观点聚类** | 语义聚类提取代表性观点 | 快速理解舆论场 |
| **趋势预测** | 基于历史数据预测话题走向 | 提前布局内容 |
| **竞品监控** | 追踪竞争账号的爆款内容 | 学习爆款密码 |
| **报告生成** | 自动生成结构化分析报告 | 辅助内容策划 |

---

## 2. 系统架构

### 2.1 五大智能引擎

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                          BettaFish 多智能体系统                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        用户查询入口 (Flask 5000)                         │ │
│  └───────────────────────────────┬─────────────────────────────────────────┘ │
│                                  │                                           │
│          ┌───────────────────────┼───────────────────────┐                   │
│          │                       │                       │                   │
│          ▼                       ▼                       ▼                   │
│  ┌───────────────┐       ┌───────────────┐       ┌───────────────┐          │
│  │  QueryEngine  │       │  MediaEngine  │       │ InsightEngine │          │
│  │   (网络搜索)   │       │  (多模态分析)  │       │  (私有数据库)  │          │
│  │               │       │               │       │               │          │
│  │ • Tavily API  │       │ • Gemini 2.5  │       │ • MindSpider  │          │
│  │ • Anspire API │       │ • 视频解析     │       │ • 情感模型     │          │
│  │ • 新闻聚合    │       │ • 图片识别     │       │ • 语义聚类     │          │
│  │               │       │               │       │               │          │
│  │ Port: 8503    │       │ Port: 8502    │       │ Port: 8501    │          │
│  └───────┬───────┘       └───────┬───────┘       └───────┬───────┘          │
│          │                       │                       │                   │
│          └───────────────────────┼───────────────────────┘                   │
│                                  │ 实时日志输出                               │
│                                  ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         ForumEngine (智能体论坛)                          │
│  │                                                                         │ │
│  │   ┌─────────────┐                      ┌─────────────────────────────┐  │ │
│  │   │ LogMonitor  │ ──监听各引擎日志──►  │      LLM Host (Qwen)        │  │ │
│  │   │  (1秒轮询)   │                      │ • 每5条消息触发一次主持     │  │ │
│  │   └─────────────┘                      │ • 识别讨论空白点            │  │ │
│  │                                        │ • 建议分析方向              │  │ │
│  │   ┌─────────────────────────────────┐  └─────────────────────────────┘  │ │
│  │   │            forum.log             │                                  │ │
│  │   │  [14:30:45] [INSIGHT] 完成热点分析...                               │ │
│  │   │  [14:30:52] [QUERY] 发现相关新闻3篇...                              │ │
│  │   │  [14:31:05] [HOST] 建议深入分析用户情绪...                          │ │
│  │   └─────────────────────────────────┘                                  │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                  │                                           │
│                                  ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        ReportEngine (报告生成)                           │ │
│  │                                                                         │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │ │
│  │  │ 模板选择 │→│ 布局设计 │→│ 预算分配 │→│ 章节生成 │→│ GraphRAG │  │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │ │
│  │                                                           │             │ │
│  │                                                           ▼             │ │
│  │  输出: HTML (交互式) / PDF / Markdown + 知识图谱可视化                   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据采集层 - MindSpider

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                        MindSpider 爬虫集群系统                                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                     BroadTopicExtraction (每小时)                        │ │
│  │                                                                         │ │
│  │  新闻API → AI关键词提取 → daily_topics表                                 │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                  │                                           │
│                                  ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                   DeepSentimentCrawling (按需/定时)                       │ │
│  │                                                                         │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │ │
│  │  │  微博   │ │  抖音   │ │ 小红书  │ │ B站    │ │ 快手   │ ...        │ │
│  │  │ Weibo   │ │ Douyin  │ │  RED    │ │Bilibili│ │Kuaishou│            │ │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │ │
│  │       │           │           │           │           │                 │ │
│  │       └───────────┴───────────┴───────────┴───────────┘                 │ │
│  │                               │                                         │ │
│  │                    Playwright 浏览器自动化                               │ │
│  │                               │                                         │ │
│  │                               ▼                                         │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │ │
│  │  │                      PostgreSQL 数据库                           │   │ │
│  │  │                                                                 │   │ │
│  │  │  • weibo_post / weibo_post_comment (千万级)                      │   │ │
│  │  │  • douyin_aweme / douyin_aweme_comment (千万级)                  │   │ │
│  │  │  • xiaohongshu_note / xiaohongshu_note_comment                  │   │ │
│  │  │  • bilibili_video / bilibili_video_comment                      │   │ │
│  │  │  • daily_topics (热点话题索引)                                   │   │ │
│  │  └─────────────────────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 核心引擎详解

#### QueryEngine - 网络搜索引擎

```yaml
功能:
  - 6种搜索类型: 新闻、研究论文、社交媒体、通用搜索等
  - 国际新闻源覆盖: 30+ 主流媒体
  - 智能反思循环: 自动识别搜索空白、补充查询

处理流程:
  FirstSearchNode → ReflectionNode → FirstSummaryNode →
  ReflectionSummaryNode → ReportFormattingNode

关键集成:
  - Tavily API (新闻聚合)
  - Anspire API (AI搜索 + 网页截图)
  - Bocha API (备选搜索)
```

#### InsightEngine - 私有数据库挖掘

```yaml
功能:
  - 热点内容发现: search_hot_content()
  - 全局话题搜索: search_topic_globally()
  - 时间范围查询: search_topic_by_date()
  - 平台定向搜索: search_topic_on_platform()
  - AI关键词优化: search_with_keyword_optimization()

情感分析模型:
  - WeiboMultilingualSentiment: 22语言支持 (生产环境)
  - WeiboSentiment_Finetuned: BERT/GPT-2 LoRA微调
  - WeiboSentiment_SmallQwen: 轻量级Qwen
  - WeiboSentiment_MachineLearning: SVM传统方法

语义聚类:
  - Sentence-Transformers 向量化
  - K-Means 聚类提取代表性样本
  - 从千万级数据中抽取典型观点
```

#### MediaEngine - 多模态分析

```yaml
功能:
  - 短视频解析: 抖音/TikTok视频内容提取
  - 图片情感识别: 视觉情绪分析
  - 结构化数据卡: 天气、股票、日历等搜索引擎数据卡
  - 22语言情感分析

技术栈:
  - Gemini 2.5 Pro (主力模型)
  - 视觉API集成
```

#### ForumEngine - 智能体协作论坛

```yaml
核心理念:
  - 多智能体协作防止单模型偏见
  - LLM主持人引导讨论方向
  - 实时日志监控 + WebSocket推送

工作流程:
  1. LogMonitor 每秒监听三大引擎日志
  2. 提取智能体"发言" (JSON格式摘要)
  3. 每5条消息触发 LLM Host 分析
  4. 主持人识别空白点、建议方向
  5. 写入 forum.log + WebSocket广播到UI
```

#### ReportEngine - 智能报告生成

```yaml
处理流程:
  1. 模板选择: 4+ Markdown模板
  2. 布局设计: 标题、目录、章节结构
  3. 预算分配: 按章节分配字数/Token
  4. 章节生成: LLM逐章撰写
  5. GraphRAG增强: 知识图谱辅助
  6. 渲染输出: HTML/PDF/Markdown

GraphRAG系统:
  - graph_builder.py: 从State+Forum构建知识图谱
  - graph_storage.py: 持久化 graphrag.json
  - query_engine.py: 按关键词/类型查询图谱
  - 输出: Vis.js 交互式图谱可视化
```

---

## 3. 数据流与工作流程

### 3.1 完整数据流

```text
用户输入查询词
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│                    Flask API Gateway                         │
│                    POST /api/search                          │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  QueryEngine  │   │  MediaEngine  │   │ InsightEngine │
│               │   │               │   │               │
│ 1. 初始搜索   │   │ 1. 初始搜索   │   │ 1. 热点查询   │
│ 2. 反思补充   │   │ 2. 视频解析   │   │ 2. 情感分析   │
│ 3. 摘要综合   │   │ 3. 图片分析   │   │ 3. 聚类采样   │
│ 4. 格式化输出 │   │ 4. 格式化输出 │   │ 4. 格式化输出 │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        │  写入日志 + MD报告 │                   │
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                       ForumEngine                            │
│                                                             │
│  LogMonitor监听 → JSON提取 → LLM Host主持 → forum.log       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      ReportEngine                            │
│                                                             │
│  模板选择 → 布局设计 → 预算分配 → 章节生成 → GraphRAG → 渲染 │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                        最终输出                              │
│                                                             │
│  • final_reports/*.html (交互式 + 知识图谱)                  │
│  • final_reports/pdf/*.pdf                                  │
│  • final_reports/md/*.md                                    │
│  • final_reports/ir/*/graphrag.json                         │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 单引擎反思循环

```text
┌────────────────────────────────────────────────────────────────────┐
│                    InsightEngine 反思循环示例                       │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  用户查询: "小米汽车舆情"                                           │
│                                                                    │
│  ┌──────────────────┐                                              │
│  │  FirstSearchNode │                                              │
│  │                  │                                              │
│  │  search_hot_content("小米汽车")                                 │
│  │  → 返回: 100条热门帖子                                          │
│  │  → 情感分析: 正面45% 中性30% 负面25%                            │
│  └────────┬─────────┘                                              │
│           │                                                        │
│           ▼                                                        │
│  ┌──────────────────┐                                              │
│  │  ReflectionNode  │                                              │
│  │                  │                                              │
│  │  LLM分析: "缺少价格讨论、竞品对比维度"                           │
│  │  → 生成补充查询: ["小米SU7价格", "小米汽车vs特斯拉"]             │
│  └────────┬─────────┘                                              │
│           │                                                        │
│           ▼                                                        │
│  ┌──────────────────┐                                              │
│  │ FirstSummaryNode │                                              │
│  │                  │                                              │
│  │  综合初步发现:                                                   │
│  │  • 核心话题: 价格、续航、品牌                                    │
│  │  • 情绪分布: 期待 > 观望 > 质疑                                  │
│  │  • 代表观点: 5个聚类样本                                         │
│  └────────┬─────────┘                                              │
│           │                                                        │
│           ▼                                                        │
│  ┌──────────────────┐                                              │
│  │ 补充搜索循环     │  (可迭代多次)                                 │
│  │                  │                                              │
│  │  search_topic_on_platform("微博", "小米SU7价格")                │
│  │  → 聚类分析 → 反思 → 继续补充...                                │
│  └────────┬─────────┘                                              │
│           │                                                        │
│           ▼                                                        │
│  ┌──────────────────────┐                                          │
│  │ ReflectionSummaryNode │                                         │
│  │                        │                                        │
│  │  最终综合报告:                                                   │
│  │  • 舆情概览                                                      │
│  │  • 情感趋势                                                      │
│  │  • 核心议题                                                      │
│  │  • 代表性观点                                                    │
│  │  • 风险预警                                                      │
│  └────────────────────────┘                                        │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 4. 与创流项目的集成方案

### 4.1 集成架构总览

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                              创流 Agent 系统                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         Agent Runtime (LangGraph)                        │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │ │
│  │  │ 选题 Agent  │  │ 写作 Agent  │  │ 优化 Agent  │  │ 发布 Agent  │    │ │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │ │
│  │         │                │                │                │            │ │
│  │         └────────────────┼────────────────┼────────────────┘            │ │
│  │                          │                │                             │ │
│  │                          ▼                ▼                             │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │ │
│  │  │                     Tool Registry (能力注册)                     │   │ │
│  │  │                                                                 │   │ │
│  │  │  内置工具:              BettaFish工具集 (新增):                  │   │ │
│  │  │  • 文案生成            • hot_topic_discovery (热点发现)         │   │ │
│  │  │  • 图片生成            • sentiment_analysis (情感分析)          │   │ │
│  │  │  • 视频脚本            • trend_prediction (趋势预测)            │   │ │
│  │  │  • 平台适配            • competitor_monitor (竞品监控)          │   │ │
│  │  │                        • audience_insight (受众洞察)            │   │ │
│  │  │                        • content_opportunity (选题机会)         │   │ │
│  │  └─────────────────────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                          │                                   │
│                                          │ 内部调用                          │
│                                          ▼                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                      BettaFish 舆情分析层                                │ │
│  │                                                                         │ │
│  │  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐                 │ │
│  │  │  InsightEngine │ │  QueryEngine  │ │  MediaEngine  │                 │ │
│  │  │   (数据库)     │ │   (网络)      │ │   (多模态)    │                 │ │
│  │  └───────┬───────┘ └───────┬───────┘ └───────┬───────┘                 │ │
│  │          │                 │                 │                          │ │
│  │          └─────────────────┼─────────────────┘                          │ │
│  │                            │                                            │ │
│  │                            ▼                                            │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │ │
│  │  │                    MindSpider 数据层                             │   │ │
│  │  │         PostgreSQL (微博/抖音/小红书/B站/快手...)                │   │ │
│  │  └─────────────────────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 BettaFish 工具集定义

```python
# backend/app/agent/tools/bettafish_tools.py

from typing import Literal
from pydantic import BaseModel, Field

class HotTopicDiscoveryInput(BaseModel):
    """热点发现工具输入"""
    platform: Literal["weibo", "douyin", "xiaohongshu", "bilibili", "all"] = "all"
    category: str | None = Field(None, description="行业分类: 科技/美妆/汽车/美食...")
    time_range: str = Field("24h", description="时间范围: 1h/6h/24h/7d")
    limit: int = Field(20, description="返回数量")


class HotTopicDiscoveryOutput(BaseModel):
    """热点发现工具输出"""
    topics: list[dict]  # [{topic, heat_score, trend, sentiment, platforms}]
    insights: str       # AI生成的热点洞察


class SentimentAnalysisInput(BaseModel):
    """情感分析工具输入"""
    topic: str = Field(..., description="分析话题/关键词")
    platform: str | None = Field(None, description="平台筛选")
    sample_size: int = Field(500, description="样本量")


class SentimentAnalysisOutput(BaseModel):
    """情感分析工具输出"""
    positive_ratio: float
    neutral_ratio: float
    negative_ratio: float
    key_opinions: list[dict]  # [{opinion, count, sentiment, examples}]
    emotion_trend: list[dict] # [{date, positive, neutral, negative}]


class TrendPredictionInput(BaseModel):
    """趋势预测工具输入"""
    topic: str
    prediction_days: int = Field(7, description="预测天数")


class TrendPredictionOutput(BaseModel):
    """趋势预测工具输出"""
    current_heat: float
    predicted_trend: Literal["rising", "stable", "declining"]
    peak_time: str | None     # 预测峰值时间
    confidence: float
    reasoning: str            # 预测依据


class CompetitorMonitorInput(BaseModel):
    """竞品监控工具输入"""
    competitor_accounts: list[str]  # 竞品账号列表
    platform: str
    time_range: str = "7d"


class CompetitorMonitorOutput(BaseModel):
    """竞品监控工具输出"""
    top_contents: list[dict]   # [{title, engagement, sentiment, publish_time}]
    content_patterns: list[str] # 爆款模式总结
    posting_schedule: dict      # 发布时间规律


class ContentOpportunityInput(BaseModel):
    """选题机会发现工具输入"""
    niche: str = Field(..., description="创作者领域")
    target_platforms: list[str]
    content_type: Literal["article", "video", "note"] = "article"


class ContentOpportunityOutput(BaseModel):
    """选题机会发现工具输出"""
    opportunities: list[dict]  # [{topic, heat, competition, opportunity_score, angle}]
    recommended_angles: list[str]  # 建议切入角度
    timing_advice: str             # 最佳发布时机


# Tool 注册
BETTAFISH_TOOLS = [
    {
        "name": "hot_topic_discovery",
        "description": "发现当前热点话题，支持按平台和行业筛选",
        "input_schema": HotTopicDiscoveryInput,
        "output_schema": HotTopicDiscoveryOutput,
    },
    {
        "name": "sentiment_analysis",
        "description": "分析特定话题的舆情情感分布和核心观点",
        "input_schema": SentimentAnalysisInput,
        "output_schema": SentimentAnalysisOutput,
    },
    {
        "name": "trend_prediction",
        "description": "预测话题未来趋势走向",
        "input_schema": TrendPredictionInput,
        "output_schema": TrendPredictionOutput,
    },
    {
        "name": "competitor_monitor",
        "description": "监控竞品账号的爆款内容和发布规律",
        "input_schema": CompetitorMonitorInput,
        "output_schema": CompetitorMonitorOutput,
    },
    {
        "name": "content_opportunity",
        "description": "基于热点和竞争分析发现选题机会",
        "input_schema": ContentOpportunityInput,
        "output_schema": ContentOpportunityOutput,
    },
]
```

### 4.3 创作工作流集成

```yaml
# agent_graphs/viral_content_workflow.yaml

apiVersion: agent/v1
kind: Graph
metadata:
  name: viral-content-workflow
  description: 爆款内容创作工作流

spec:
  nodes:
    # 1. 热点发现阶段
    - name: discover_hot_topics
      tool: hot_topic_discovery
      params:
        platform: "${input.target_platform}"
        category: "${input.niche}"
        time_range: "24h"
        limit: 30

    # 2. 选题机会分析
    - name: find_opportunities
      tool: content_opportunity
      params:
        niche: "${input.niche}"
        target_platforms: ["${input.target_platform}"]
        content_type: "${input.content_type}"

    # 3. 情感与观点分析
    - name: analyze_sentiment
      tool: sentiment_analysis
      params:
        topic: "${state.selected_topic}"
        platform: "${input.target_platform}"
        sample_size: 1000

    # 4. 竞品分析 (可选)
    - name: check_competitors
      tool: competitor_monitor
      condition: "${input.competitor_accounts != null}"
      params:
        competitor_accounts: "${input.competitor_accounts}"
        platform: "${input.target_platform}"

    # 5. 选题决策 (LLM节点)
    - name: select_topic
      type: llm
      prompt: |
        基于以下分析，选择最佳选题:

        热点话题: ${state.hot_topics}
        选题机会: ${state.opportunities}
        情感分析: ${state.sentiment_result}
        竞品情况: ${state.competitor_insights}

        选择标准:
        1. 热度足够高 (heat_score > 70)
        2. 竞争适中 (不要太卷)
        3. 有独特切入角度
        4. 符合创作者定位

        输出:
        - selected_topic: 选定话题
        - angle: 切入角度
        - hook: 开篇钩子
        - key_points: 核心要点

    # 6. 内容生成
    - name: generate_content
      type: llm
      prompt: |
        创作一篇${input.content_type}内容:

        话题: ${state.selected_topic}
        角度: ${state.angle}
        开篇钩子: ${state.hook}
        核心要点: ${state.key_points}

        目标平台: ${input.target_platform}

        舆情洞察 (融入内容):
        - 用户关心的点: ${state.key_opinions}
        - 情绪倾向: ${state.sentiment_summary}

        要求:
        1. 标题要有吸引力
        2. 开篇3秒抓住注意力
        3. 内容要有信息增量
        4. 结尾引导互动

    # 7. 平台适配
    - name: adapt_for_platform
      tool: platform_content_adapter
      params:
        content: "${state.generated_content}"
        platform: "${input.target_platform}"

    # 8. 发布时机建议
    - name: suggest_publish_time
      tool: trend_prediction
      params:
        topic: "${state.selected_topic}"
        prediction_days: 3

  edges:
    - from: START
      to: discover_hot_topics
    - from: discover_hot_topics
      to: find_opportunities
    - from: find_opportunities
      to: analyze_sentiment
    - from: analyze_sentiment
      to: check_competitors
      condition: "${input.competitor_accounts != null}"
    - from: analyze_sentiment
      to: select_topic
      condition: "${input.competitor_accounts == null}"
    - from: check_competitors
      to: select_topic
    - from: select_topic
      to: generate_content
    - from: generate_content
      to: adapt_for_platform
    - from: adapt_for_platform
      to: suggest_publish_time
    - from: suggest_publish_time
      to: END
```

---

## 5. 核心应用场景

### 5.1 热点追踪 - 第一时间捕捉选题

```text
┌────────────────────────────────────────────────────────────────────────┐
│                          热点追踪工作流                                 │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  定时任务 (每小时)                                                      │
│       │                                                                │
│       ▼                                                                │
│  ┌─────────────────┐                                                   │
│  │ MindSpider      │                                                   │
│  │ 抓取各平台热搜   │                                                   │
│  └────────┬────────┘                                                   │
│           │                                                            │
│           ▼                                                            │
│  ┌─────────────────┐                                                   │
│  │ InsightEngine   │                                                   │
│  │ 热点聚类分析    │                                                   │
│  └────────┬────────┘                                                   │
│           │                                                            │
│           ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                      热点评估矩阵                                │  │
│  │                                                                 │  │
│  │  热度分数 = 搜索量×0.3 + 讨论量×0.3 + 增长率×0.2 + 平台覆盖×0.2 │  │
│  │                                                                 │  │
│  │  ┌─────────┬───────┬───────┬───────┬───────────┐               │  │
│  │  │  话题   │ 热度  │ 趋势  │ 情绪  │ 推荐指数  │               │  │
│  │  ├─────────┼───────┼───────┼───────┼───────────┤               │  │
│  │  │ 话题A   │  95   │  ↑↑   │ 正面  │  ⭐⭐⭐⭐⭐ │               │  │
│  │  │ 话题B   │  87   │  ↑    │ 中性  │  ⭐⭐⭐⭐  │               │  │
│  │  │ 话题C   │  82   │  →    │ 负面  │  ⭐⭐⭐   │               │  │
│  │  └─────────┴───────┴───────┴───────┴───────────┘               │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│           │                                                            │
│           ▼                                                            │
│  ┌─────────────────┐                                                   │
│  │ 推送通知        │                                                   │
│  │ "发现高潜力话题"│                                                   │
│  └─────────────────┘                                                   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### 5.2 情感洞察 - 精准把握用户痛点

```python
# 情感分析应用示例

async def get_content_angles(topic: str) -> dict:
    """基于情感分析获取内容切入角度"""

    # 1. 获取情感分析结果
    sentiment_result = await sentiment_analysis(
        topic=topic,
        sample_size=1000
    )

    # 2. 提取核心观点
    key_opinions = sentiment_result.key_opinions

    # 3. 分析内容机会
    angles = []

    for opinion in key_opinions:
        if opinion["sentiment"] == "negative":
            # 负面观点 → 解决方案型内容
            angles.append({
                "type": "solution",
                "pain_point": opinion["opinion"],
                "angle": f"如何解决{opinion['opinion']}",
                "potential": "high"  # 负面痛点=高需求
            })
        elif opinion["sentiment"] == "positive":
            # 正面观点 → 共鸣型内容
            angles.append({
                "type": "resonance",
                "highlight": opinion["opinion"],
                "angle": f"为什么{opinion['opinion']}",
                "potential": "medium"
            })
        else:
            # 中性观点 → 科普型内容
            angles.append({
                "type": "education",
                "topic": opinion["opinion"],
                "angle": f"关于{opinion['opinion']}你需要知道的",
                "potential": "medium"
            })

    return {
        "sentiment_summary": {
            "positive": sentiment_result.positive_ratio,
            "neutral": sentiment_result.neutral_ratio,
            "negative": sentiment_result.negative_ratio,
        },
        "recommended_angles": sorted(angles, key=lambda x: x["potential"], reverse=True),
        "timing": "当前讨论热烈，建议24小时内发布" if sentiment_result.positive_ratio + sentiment_result.negative_ratio > 0.6 else "话题较平淡，可等待引爆点"
    }
```

### 5.3 行业分析 - 垂直领域深度洞察

```yaml
# 行业分析模板

行业分析报告结构:
  1. 行业热点概览:
     - 本周热门话题 TOP10
     - 热度趋势曲线
     - 平台分布分析

  2. 用户情绪画像:
     - 情感分布
     - 核心关注点
     - 痛点排行

  3. 竞品内容分析:
     - 头部账号爆款
     - 内容形式分布
     - 发布时间规律

  4. 选题机会矩阵:
     - 高热度 + 低竞争 = 黄金选题
     - 高热度 + 高竞争 = 需要差异化
     - 低热度 + 低竞争 = 蓝海潜力

  5. 创作建议:
     - 推荐话题列表
     - 建议切入角度
     - 最佳发布时机
```

### 5.4 爆款公式 - 数据驱动创作

```text
┌────────────────────────────────────────────────────────────────────────┐
│                           爆款内容公式                                  │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   爆款指数 = 话题热度 × 情绪共鸣 × 信息增量 × 发布时机                  │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐  │
│   │                    BettaFish 数据支撑                           │  │
│   ├────────────────────────────────────────────────────────────────┤  │
│   │                                                                │  │
│   │  话题热度:                                                      │  │
│   │    • MindSpider 实时热搜数据                                   │  │
│   │    • 跨平台热度聚合                                            │  │
│   │    • 趋势预测 (上升期 vs 衰退期)                               │  │
│   │                                                                │  │
│   │  情绪共鸣:                                                      │  │
│   │    • 情感分析识别用户痛点                                      │  │
│   │    • 高频观点聚类                                              │  │
│   │    • 情绪词云分析                                              │  │
│   │                                                                │  │
│   │  信息增量:                                                      │  │
│   │    • 竞品内容分析 (已有内容)                                   │  │
│   │    • 信息空白点发现                                            │  │
│   │    • 差异化角度建议                                            │  │
│   │                                                                │  │
│   │  发布时机:                                                      │  │
│   │    • 热度曲线预测                                              │  │
│   │    • 竞品发布时间分析                                          │  │
│   │    • 平台流量高峰分析                                          │  │
│   │                                                                │  │
│   └────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐  │
│   │                    Agent 创作决策                               │  │
│   ├────────────────────────────────────────────────────────────────┤  │
│   │                                                                │  │
│   │  选题决策:                                                      │  │
│   │    IF 热度>80 AND 上升趋势 AND 竞争度<60 → 立即创作             │  │
│   │    IF 热度>70 AND 稳定趋势 AND 有差异角度 → 建议创作            │  │
│   │    IF 热度<50 OR 下降趋势 → 等待或放弃                         │  │
│   │                                                                │  │
│   │  内容策略:                                                      │  │
│   │    IF 负面情绪>40% → 解决方案型内容                            │  │
│   │    IF 正面情绪>60% → 共鸣放大型内容                            │  │
│   │    IF 信息空白明显 → 科普干货型内容                            │  │
│   │                                                                │  │
│   │  发布决策:                                                      │  │
│   │    IF 预测48小时内达峰 → 立即发布                              │  │
│   │    IF 预测7天后达峰 → 提前24小时发布                           │  │
│   │    IF 已过峰值 → 放弃或转其他话题                              │  │
│   │                                                                │  │
│   └────────────────────────────────────────────────────────────────┘  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 6. 技术集成细节

### 6.1 服务调用方式

```python
# backend/app/agent/tools/bettafish_client.py

import httpx
from typing import Any

class BettaFishClient:
    """BettaFish 服务客户端"""

    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)

    async def search(self, query: str) -> dict:
        """触发全量搜索 (3引擎并行)"""
        response = await self.client.post(
            f"{self.base_url}/api/search",
            json={"query": query}
        )
        return response.json()

    async def get_hot_topics(
        self,
        platform: str = "all",
        category: str | None = None,
        limit: int = 20
    ) -> list[dict]:
        """获取热点话题"""
        # 调用 InsightEngine 的 search_hot_content
        response = await self.client.post(
            f"{self.base_url}/api/insight/hot",
            json={
                "platform": platform,
                "category": category,
                "limit": limit
            }
        )
        return response.json()["topics"]

    async def analyze_sentiment(
        self,
        topic: str,
        platform: str | None = None,
        sample_size: int = 500
    ) -> dict:
        """情感分析"""
        response = await self.client.post(
            f"{self.base_url}/api/insight/sentiment",
            json={
                "topic": topic,
                "platform": platform,
                "sample_size": sample_size
            }
        )
        return response.json()

    async def generate_report(
        self,
        query: str,
        template: str = "default"
    ) -> dict:
        """生成完整报告"""
        # 1. 启动报告生成
        start_response = await self.client.post(
            f"{self.base_url}/api/report/generate",
            json={"query": query, "template": template}
        )
        task_id = start_response.json()["task_id"]

        # 2. 轮询进度或使用SSE
        # ...

        # 3. 获取结果
        result = await self.client.get(
            f"{self.base_url}/api/report/result/{task_id}"
        )
        return result.json()


# Tool 实现
async def hot_topic_discovery(
    platform: str = "all",
    category: str | None = None,
    time_range: str = "24h",
    limit: int = 20
) -> dict:
    """热点发现工具"""
    client = BettaFishClient()

    topics = await client.get_hot_topics(
        platform=platform,
        category=category,
        limit=limit
    )

    # 生成洞察
    insights = await generate_topic_insights(topics)

    return {
        "topics": topics,
        "insights": insights
    }
```

### 6.2 数据库共享方案

```yaml
# 两种方案

方案A: API调用 (推荐)
  优点:
    - 解耦清晰
    - 便于独立扩展
    - 无需共享数据库连接
  缺点:
    - 网络延迟
    - 需要维护API

方案B: 数据库直连
  优点:
    - 查询更快
    - 实时性更高
  缺点:
    - 耦合紧密
    - 需要共享数据库配置

推荐: 方案A (API调用)
  - BettaFish 作为独立微服务运行
  - 创流通过 HTTP API 调用
  - 未来可考虑 gRPC 提升性能
```

### 6.3 部署架构

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                              Docker Compose 部署                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                              共享网络                                    │ │
│  │                                                                         │ │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐               │ │
│  │  │ creatorflow   │  │  bettafish    │  │  mindspider   │               │ │
│  │  │   (5001)      │  │   (5000)      │  │   (Worker)    │               │ │
│  │  │               │  │               │  │               │               │ │
│  │  │ FastAPI       │  │ Flask         │  │ Playwright    │               │ │
│  │  │ Agent Runtime │  │ 3 Engines     │  │ 爬虫集群      │               │ │
│  │  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘               │ │
│  │          │                  │                  │                        │ │
│  │          └──────────────────┼──────────────────┘                        │ │
│  │                             │                                           │ │
│  │  ┌──────────────────────────┴──────────────────────────────────────┐   │ │
│  │  │                      PostgreSQL (5432)                          │   │ │
│  │  │                                                                 │   │ │
│  │  │  creatorflow_db  │  bettafish_db (共享或独立)                   │   │ │
│  │  └─────────────────────────────────────────────────────────────────┘   │ │
│  │                                                                         │ │
│  │  ┌─────────────────┐  ┌─────────────────┐                              │ │
│  │  │  Redis (6379)   │  │  MinIO (9000)   │                              │ │
│  │  │ Cache + Broker  │  │ 媒体存储        │                              │ │
│  │  └─────────────────┘  └─────────────────┘                              │ │
│  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

```yaml
# docker-compose.yml 示例

version: '3.8'

services:
  creatorflow:
    build: ./cloud-backend
    ports:
      - "5001:5001"
    environment:
      - BETTAFISH_URL=http://bettafish:5000
    depends_on:
      - bettafish
      - postgres
      - redis

  bettafish:
    build: ./BettaFish
    ports:
      - "5000:5000"
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
    depends_on:
      - postgres

  mindspider:
    build: ./BettaFish/MindSpider
    environment:
      - DB_HOST=postgres
    depends_on:
      - postgres

  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=bettafish
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=secret

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

## 7. 使用示例

### 7.1 命令行快速测试

```bash
# 启动 BettaFish
cd BettaFish
python app.py

# 热点查询
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "小米汽车"}'

# 获取热点话题
curl -X POST http://localhost:5000/api/insight/hot \
  -H "Content-Type: application/json" \
  -d '{"platform": "weibo", "limit": 10}'

# 情感分析
curl -X POST http://localhost:5000/api/insight/sentiment \
  -H "Content-Type: application/json" \
  -d '{"topic": "小米SU7", "sample_size": 500}'
```

### 7.2 Agent 工作流调用示例

```python
# 在创流 Agent 中使用 BettaFish 工具

from langchain.tools import Tool
from app.agent.tools.bettafish_tools import (
    hot_topic_discovery,
    sentiment_analysis,
    content_opportunity
)

# 定义工具
tools = [
    Tool(
        name="热点发现",
        func=hot_topic_discovery,
        description="发现当前各平台热门话题"
    ),
    Tool(
        name="情感分析",
        func=sentiment_analysis,
        description="分析话题的用户情感和核心观点"
    ),
    Tool(
        name="选题机会",
        func=content_opportunity,
        description="基于热点和竞争分析发现创作机会"
    ),
]

# Agent 使用示例
async def create_viral_content(niche: str, platform: str):
    """创作爆款内容"""

    # 1. 发现热点
    hot_topics = await hot_topic_discovery(
        platform=platform,
        category=niche,
        limit=20
    )

    # 2. 选择最佳话题
    best_topic = select_best_topic(hot_topics["topics"])

    # 3. 分析情感
    sentiment = await sentiment_analysis(
        topic=best_topic["name"],
        platform=platform
    )

    # 4. 获取创作角度
    opportunities = await content_opportunity(
        niche=niche,
        target_platforms=[platform]
    )

    # 5. 基于洞察生成内容
    content = await generate_content_with_insights(
        topic=best_topic,
        sentiment=sentiment,
        angles=opportunities["recommended_angles"]
    )

    return content
```

---

## 8. 总结

### 8.1 BettaFish 核心价值

| 能力 | 对创作的价值 | 实现方式 |
|------|-------------|---------|
| 热点发现 | 第一时间捕捉爆款选题 | MindSpider + InsightEngine |
| 情感分析 | 精准把握用户痛点 | 22语言情感模型 + 语义聚类 |
| 趋势预测 | 提前布局内容 | 历史数据 + 预测模型 |
| 竞品监控 | 学习爆款密码 | 跨平台内容追踪 |
| 报告生成 | 辅助内容策划 | ReportEngine + GraphRAG |

### 8.2 集成收益

```text
创流 + BettaFish = 数据驱动的内容创作闭环

┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   传统创作:  灵感 → 创作 → 发布 → 看数据                    │
│                ↓                                            │
│            凭感觉                                           │
│                                                             │
│   AI创作:   数据 → 洞察 → 创作 → 优化 → 发布 → 复盘         │
│              ↓      ↓                ↓                      │
│          BettaFish  Agent           BettaFish               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 8.3 下一步行动

1. **Phase 1**: 部署 BettaFish 服务，配置数据库和爬虫
2. **Phase 2**: 开发 BettaFish Tool 适配层
3. **Phase 3**: 集成到创流 Agent Runtime
4. **Phase 4**: 构建"热点追踪 → 创作 → 发布"完整工作流
5. **Phase 5**: 基于反馈持续优化

---

## 相关文档

- [系统架构](./01-系统架构.md)
- [Agent Runtime](./05-Agent-Runtime.md)
- [AI工作流](./07-AI工作流.md)
