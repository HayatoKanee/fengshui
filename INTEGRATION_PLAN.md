# 命理AI助手 - 融合方案

## 🎯 目标

将「对话式AI交互」和「K线可视化」概念融合到现有 myfate.org 项目中，提升用户体验。

---

## 📊 现有项目 vs 新概念对比

| 功能 | 现有项目 (myfate.org) | 新概念 (命理AI助手) | 融合方案 |
|-----|---------------------|-------------------|---------|
| 八字分析 | ✅ 完整实现 | 需要 | 复用现有服务 |
| 五行分析 | ✅ 完整实现 | 需要 | 复用现有服务 |
| 流年运势 | ✅ LiunianAnalysisService | 需要 | 复用并增强展示 |
| 日历 | ✅ CalendarService | 需要 | 复用 |
| 飞星 | ✅ FeiXingService | 可选 | 保留 |
| 用户档案 | ✅ UserProfile | 需要 | 复用 |
| **AI对话** | ❌ 无 | ⭐ 核心 | **新增** |
| **K线图** | ❌ 无 | ⭐ 核心 | **新增** |
| **合婚** | ❌ 无 | 需要 | **新增** |
| **今日运势** | ❌ 无 | 需要 | **新增** |

---

## 🏗️ 融合架构

```
┌─────────────────────────────────────────────────────────────┐
│                     前端 (React + HTMX)                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────┐ │
│  │ 首页    │ │ AI对话  │ │ K线图   │ │ 合婚    │ │ 原有  │ │
│  │ (新)    │ │ (新)    │ │ (新)    │ │ (新)    │ │ 页面  │ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └───────┘ │
│                         │                                   │
│         ┌───────────────┴───────────────┐                  │
│         │     ChatWidget (全局组件)      │ ← 每个页面都有   │
│         │     底部对话入口               │                  │
│         └───────────────────────────────┘                  │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                     后端 (Django)                            │
│                                                             │
│  ┌─────────────────── 新增模块 ───────────────────┐         │
│  │                                                │         │
│  │  chat/                    # AI对话模块         │         │
│  │  ├── views.py            # WebSocket/API      │         │
│  │  ├── services/                                │         │
│  │  │   ├── ai_service.py   # LLM调用           │         │
│  │  │   ├── tool_service.py # 工具调用          │         │
│  │  │   └── context_service.py # 上下文管理     │         │
│  │  └── models.py           # 对话历史          │         │
│  │                                                │         │
│  │  kline/                   # K线模块           │         │
│  │  ├── views.py                                 │         │
│  │  └── services/                                │         │
│  │      └── kline_service.py # K线数据生成      │         │
│  │                                                │         │
│  │  match/                   # 合婚模块          │         │
│  │  ├── views.py                                 │         │
│  │  └── services/                                │         │
│  │      └── match_service.py # 配对分析         │         │
│  │                                                │         │
│  └────────────────────────────────────────────────┘         │
│                             │                               │
│  ┌──────────────── 复用现有模块 ─────────────────┐          │
│  │                                               │          │
│  │  bazi/domain/services/                        │          │
│  │  ├── BaziAnalysisService    ← AI工具调用     │          │
│  │  ├── WuxingCalculator       ← AI工具调用     │          │
│  │  ├── ShishenCalculator      ← AI工具调用     │          │
│  │  ├── LiunianAnalysisService ← AI工具调用     │          │
│  │  └── DayQualityService      ← AI工具调用     │          │
│  │                                               │          │
│  └───────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 新增文件结构

```
fengshui/
├── bazi/
│   ├── ... (保持不变)
│   │
│   ├── chat/                          # 🆕 AI对话模块
│   │   ├── __init__.py
│   │   ├── models.py                  # 对话历史模型
│   │   ├── views.py                   # API视图
│   │   ├── urls.py
│   │   ├── consumers.py               # WebSocket (可选)
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── ai_service.py          # LLM服务
│   │       ├── tool_registry.py       # 工具注册
│   │       └── tools/
│   │           ├── __init__.py
│   │           ├── bazi_tool.py       # 八字分析工具
│   │           ├── fortune_tool.py    # 运势分析工具
│   │           ├── kline_tool.py      # K线生成工具
│   │           └── match_tool.py      # 合婚分析工具
│   │
│   ├── kline/                         # 🆕 K线模块
│   │   ├── __init__.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── services/
│   │       ├── __init__.py
│   │       └── kline_calculator.py    # K线数据计算
│   │
│   └── match/                         # 🆕 合婚模块
│       ├── __init__.py
│       ├── views.py
│       ├── urls.py
│       └── services/
│           ├── __init__.py
│           └── match_calculator.py    # 配对计算
│
├── frontend/
│   └── src/
│       ├── ... (保持不变)
│       │
│       ├── components/                # 🆕 新组件
│       │   ├── ChatWidget/            # 全局对话组件
│       │   │   ├── ChatWidget.tsx
│       │   │   ├── ChatInput.tsx
│       │   │   ├── MessageBubble.tsx
│       │   │   └── ChartCard.tsx
│       │   ├── KLineChart/            # K线图组件
│       │   │   └── KLineChart.tsx
│       │   └── MatchCard/             # 合婚结果组件
│       │       └── MatchCard.tsx
│       │
│       └── pages/                     # 🆕 新页面
│           ├── HomePage.tsx           # 新首页
│           ├── ChatPage.tsx           # 全屏对话
│           ├── KLinePage.tsx          # K线详情
│           └── MatchPage.tsx          # 合婚页面
│
└── templates/
    ├── ... (保持不变)
    │
    ├── home_new.html                  # 🆕 新首页模板
    ├── chat.html                      # 🆕 对话页面模板
    ├── kline.html                     # 🆕 K线页面模板
    └── match.html                     # 🆕 合婚页面模板
```

---

## 🔧 核心实现方案

### 1. AI对话服务 (chat/services/ai_service.py)

```python
from anthropic import Anthropic
from typing import Generator
import json

class AIService:
    """AI对话服务 - 调用Claude API"""

    def __init__(self):
        self.client = Anthropic()
        self.tools = self._register_tools()

    def _register_tools(self):
        """注册AI可调用的工具"""
        return [
            {
                "name": "analyze_bazi",
                "description": "分析用户的八字命盘，包括四柱、五行、十神等",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "birth_year": {"type": "integer"},
                        "birth_month": {"type": "integer"},
                        "birth_day": {"type": "integer"},
                        "birth_hour": {"type": "integer"},
                        "is_male": {"type": "boolean"}
                    },
                    "required": ["birth_year", "birth_month", "birth_day", "birth_hour"]
                }
            },
            {
                "name": "generate_kline",
                "description": "生成用户的人生K线图数据",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "profile_id": {"type": "integer"}
                    },
                    "required": ["profile_id"]
                }
            },
            {
                "name": "analyze_fortune",
                "description": "分析特定时间段的运势",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "profile_id": {"type": "integer"},
                        "year": {"type": "integer"},
                        "month": {"type": "integer", "description": "可选，不传则分析全年"}
                    },
                    "required": ["profile_id", "year"]
                }
            },
            {
                "name": "match_compatibility",
                "description": "分析两个人的八字配对",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "profile_id_1": {"type": "integer"},
                        "profile_id_2": {"type": "integer"}
                    },
                    "required": ["profile_id_1", "profile_id_2"]
                }
            }
        ]

    def chat(self, messages: list, profile_id: int = None) -> Generator:
        """
        与AI对话，支持流式输出

        Args:
            messages: 对话历史
            profile_id: 当前用户档案ID

        Yields:
            AI回复的片段
        """
        system_prompt = self._build_system_prompt(profile_id)

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            tools=self.tools,
            messages=messages,
            stream=True
        )

        for event in response:
            if event.type == "content_block_delta":
                yield event.delta
            elif event.type == "tool_use":
                # 处理工具调用
                tool_result = self._execute_tool(event.name, event.input)
                yield {"type": "tool_result", "data": tool_result}

    def _build_system_prompt(self, profile_id: int = None) -> str:
        """构建系统提示词"""
        base_prompt = """你是一个专业的命理AI助手，精通八字、五行、十神等中国传统命理学。

你的特点：
1. 用通俗易懂的语言解释命理知识，避免过多专业术语
2. 结合用户的具体情况给出个性化建议
3. 回答时既要有传统命理的依据，也要实用可行
4. 适时使用可视化（如K线图）帮助用户理解

当用户询问运势相关问题时：
- 如果需要分析八字，调用 analyze_bazi 工具
- 如果需要展示人生运势走向，调用 generate_kline 工具
- 如果需要分析特定时间运势，调用 analyze_fortune 工具
- 如果需要配对分析，调用 match_compatibility 工具

回复格式建议：
- 先给出核心结论
- 再解释依据
- 最后给出建议
- 如有图表，在适当位置嵌入
"""

        if profile_id:
            # 加载用户档案信息作为上下文
            base_prompt += f"\n\n用户已有档案ID: {profile_id}"

        return base_prompt

    def _execute_tool(self, tool_name: str, tool_input: dict) -> dict:
        """执行工具调用"""
        from .tools import bazi_tool, fortune_tool, kline_tool, match_tool

        tool_map = {
            "analyze_bazi": bazi_tool.analyze,
            "generate_kline": kline_tool.generate,
            "analyze_fortune": fortune_tool.analyze,
            "match_compatibility": match_tool.analyze
        }

        if tool_name in tool_map:
            return tool_map[tool_name](**tool_input)

        return {"error": f"Unknown tool: {tool_name}"}
```

### 2. K线计算服务 (kline/services/kline_calculator.py)

```python
from bazi.domain.services import BaziAnalysisService, LiunianAnalysisService
from bazi.infrastructure.di.container import get_container
from typing import List, Dict

class KLineCalculator:
    """人生K线图计算器"""

    def __init__(self):
        container = get_container()
        self.bazi_service = container.bazi_analysis_service
        self.liunian_service = container.liunian_analysis_service

    def calculate(self, profile) -> Dict:
        """
        计算完整的人生K线数据

        Returns:
            {
                "data_points": [
                    {"age": 20, "score": 65, "phase": "积累期", "description": "..."},
                    {"age": 25, "score": 70, "phase": "积累期", "description": "..."},
                    ...
                ],
                "current_age": 34,
                "current_phase": {
                    "name": "上升期",
                    "range": [34, 44],
                    "keywords": ["事业突破", "贵人助力"],
                    "description": "这是你人生中最重要的黄金十年..."
                },
                "phases": [
                    {"range": [20, 30], "name": "积累期", "trend": "up"},
                    {"range": [30, 40], "name": "上升期", "trend": "up"},
                    ...
                ]
            }
        """
        # 1. 获取八字
        bazi = self.bazi_service.analyze(
            profile.birth_year,
            profile.birth_month,
            profile.birth_day,
            profile.birth_hour,
            profile.is_male
        )

        # 2. 计算各年龄段运势
        data_points = []
        current_year = 2024
        birth_year = profile.birth_year

        for age in range(20, 81, 5):
            target_year = birth_year + age

            # 使用流年服务计算该年运势
            liunian = self.liunian_service.analyze(bazi, target_year)

            # 计算综合评分
            score = self._calculate_score(bazi, liunian)

            data_points.append({
                "age": age,
                "year": target_year,
                "score": score,
                "phase": self._get_phase_name(score, age),
                "description": self._generate_description(bazi, liunian, age)
            })

        # 3. 识别人生阶段
        phases = self._identify_phases(data_points)

        # 4. 确定当前阶段
        current_age = current_year - birth_year
        current_phase = self._get_current_phase(phases, current_age)

        return {
            "data_points": data_points,
            "current_age": current_age,
            "current_phase": current_phase,
            "phases": phases
        }

    def _calculate_score(self, bazi, liunian) -> int:
        """计算运势评分 (0-100)"""
        # 基于五行平衡、十神配置、流年配合等计算
        base_score = 60

        # 1. 日主强弱影响
        if bazi.is_day_master_strong:
            base_score += 5

        # 2. 五行平衡影响
        wuxing_balance = self._calc_wuxing_balance(bazi)
        base_score += wuxing_balance * 10

        # 3. 流年配合影响
        liunian_factor = self._calc_liunian_factor(bazi, liunian)
        base_score += liunian_factor * 15

        return min(100, max(0, int(base_score)))

    def _identify_phases(self, data_points: List[Dict]) -> List[Dict]:
        """识别人生阶段"""
        phases = []
        # 根据分数走势划分阶段
        # ... 实现阶段识别逻辑
        return phases

    def _get_current_phase(self, phases: List[Dict], current_age: int) -> Dict:
        """获取当前所处阶段"""
        for phase in phases:
            if phase["range"][0] <= current_age <= phase["range"][1]:
                return phase
        return phases[-1] if phases else None
```

### 3. 前端对话组件 (frontend/src/components/ChatWidget/ChatWidget.tsx)

```typescript
import React, { useState, useRef, useEffect } from 'react';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';
import { ChartCard } from './ChartCard';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  attachments?: Attachment[];
}

interface Attachment {
  type: 'chart' | 'quickActions';
  data: any;
}

export const ChatWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (content: string) => {
    // 添加用户消息
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // 调用后端API
      const response = await fetch('/api/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
          messages: [...messages, userMessage].map(m => ({
            role: m.role,
            content: m.content
          }))
        })
      });

      const data = await response.json();

      // 添加AI回复
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.content,
        attachments: data.attachments
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 收起状态 - 显示在页面底部
  if (!isOpen) {
    return (
      <div
        className="fixed bottom-4 left-4 right-4 z-50"
        onClick={() => { setIsOpen(true); setIsFullScreen(true); }}
      >
        <div className="bg-base-200 rounded-full px-4 py-3 flex items-center gap-2 cursor-pointer hover:bg-base-300 transition shadow-lg">
          <span className="text-xl">💬</span>
          <span className="text-base-content/60 flex-1">有什么想问的？点击和我聊聊...</span>
          <span className="text-xl">🎤</span>
        </div>
      </div>
    );
  }

  // 全屏对话模式
  return (
    <div className={`fixed inset-0 z-50 bg-base-100 flex flex-col ${isFullScreen ? '' : 'hidden'}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-base-300">
        <button
          className="btn btn-ghost btn-circle"
          onClick={() => { setIsOpen(false); setIsFullScreen(false); }}
        >
          ←
        </button>
        <h2 className="text-lg font-bold">AI命理助手</h2>
        <div className="w-10"></div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <MessageBubble
            role="assistant"
            content="你好！我是你的命理AI助手 ✨ 我可以帮你了解事业财运、感情婚姻、健康运势等。你现在最想了解哪方面？"
          />
        )}

        {messages.map(msg => (
          <React.Fragment key={msg.id}>
            <MessageBubble role={msg.role} content={msg.content} />
            {msg.attachments?.map((att, i) => (
              att.type === 'chart' ? (
                <ChartCard key={i} {...att.data} />
              ) : null
            ))}
          </React.Fragment>
        ))}

        {isLoading && (
          <div className="flex gap-1 p-3">
            <span className="loading loading-dots loading-sm"></span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
};

function getCsrfToken(): string {
  return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
}
```

---

## 🗺️ URL路由规划

```python
# fengshui/urls.py 新增路由

urlpatterns = [
    # ... 保留现有路由

    # 🆕 新增路由
    path('', views.home_new, name='home_new'),           # 新首页
    path('chat/', views.chat_view, name='chat'),          # 对话页面
    path('api/chat/', views.chat_api, name='chat_api'),   # 对话API
    path('kline/', views.kline_view, name='kline'),       # K线页面
    path('api/kline/', views.kline_api, name='kline_api'),# K线API
    path('match/', views.match_view, name='match'),       # 合婚页面
    path('api/match/', views.match_api, name='match_api'),# 合婚API
]
```

---

## 📅 实施计划

### Phase 1: 基础对话功能 (1-2周)

| 任务 | 说明 |
|-----|------|
| 创建 chat 模块 | 模型、视图、路由 |
| 实现 AIService | 对接 Claude API |
| 实现基础工具 | bazi_tool, fortune_tool |
| 创建 ChatWidget | 前端对话组件 |
| 集成到现有页面 | 每个页面添加对话入口 |

### Phase 2: K线可视化 (1周)

| 任务 | 说明 |
|-----|------|
| 创建 kline 模块 | 计算服务 |
| 实现 KLineChart | 使用 Chart.js/ECharts |
| K线页面 | 完整的K线详情页 |
| AI工具集成 | generate_kline 工具 |

### Phase 3: 合婚功能 (1周)

| 任务 | 说明 |
|-----|------|
| 创建 match 模块 | 配对计算服务 |
| 合婚页面 | 输入 + 结果展示 |
| AI工具集成 | match_compatibility 工具 |

### Phase 4: 新首页 + 优化 (1周)

| 任务 | 说明 |
|-----|------|
| 新首页设计 | 今日运势 + 快捷入口 |
| 性能优化 | 缓存、懒加载 |
| 测试 | 端到端测试 |

---

## 💡 技术要点

### 1. 复用现有服务

```python
# 在 AI 工具中复用现有服务
from bazi.infrastructure.di.container import get_container

def analyze_bazi(**kwargs):
    container = get_container()
    service = container.bazi_analysis_service

    result = service.analyze(
        kwargs['birth_year'],
        kwargs['birth_month'],
        kwargs['birth_day'],
        kwargs['birth_hour'],
        kwargs.get('is_male', True)
    )

    # 转换为AI友好的格式
    return {
        "bazi": str(result.bazi),
        "day_master": result.day_master,
        "wuxing_strength": result.wuxing_strength,
        "shishen": result.shishen,
        # ...
    }
```

### 2. 对话历史存储

```python
# chat/models.py
from django.db import models
from django.contrib.auth.models import User

class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    role = models.CharField(max_length=20)  # user / assistant
    content = models.TextField()
    attachments = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
```

### 3. 保持现有页面不变

新功能通过**增量方式**添加：
- 现有页面保持不变，只添加底部对话入口
- 新首页作为可选项，可通过配置切换
- 渐进式迁移，不影响现有用户

---

## ✅ 下一步

1. 确认方案后，我可以开始创建代码文件
2. 优先实现 AI 对话模块（核心功能）
3. 逐步添加 K线、合婚等功能

需要我开始实现哪个部分？
