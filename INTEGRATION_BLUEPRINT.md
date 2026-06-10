# 天机 × novel-agent 整合蓝图

> **核心理念**：天机为体（Agent 框架/工具系统/LLM 抽象层），novel-agent 为用（领域模型/Web UI/创作工作流）
>
> 目标：一份代码、两套 UI（桌面 PySide6 + Web）、一个数据层、Agent 驱动创作

---

## 现状对比

| 维度 | 天机 (TIANJI) | novel-agent | 整合方案 |
|------|-------------|-------------|---------|
| **LLM 集成** | DeepSeek/OpenAI/Ollama 全支持，配置化 | 仅 openai.ChatCompletion | 保留天机 LLM 层 |
| **Agent 框架** | 工具注册、编排、记忆系统完善 | 无 Agent，直接 API 调 LLM | 保留天机 Agent |
| **领域模型** | 扁平 dict，storycraft/domain.py 有初步模型 | DDD 模型：Story/Chapter/WorldBuilding | 以 novel-agent 模型为准升级 |
| **数据存储** | `data/novels/*.json` + `data/memory.json` | `novels/*.json` | 统一到天机的 `data/novels/` |
| **故事元数据** | title/genre/description/outline/world/characters/chapters | title/author/genre/description/outline/tone/pov/target_audience/status/tags | 合并字段，兼容两边 |
| **章节模型** | id/title/content/created_at/updated_at | id/title/content/word_count/notes/status/order_index | 扩展章节模型 |
| **世界观** | world 嵌套 dict (name/desc/rules/background) | WorldBuilding 独立实体 (5 分类) | 引入 WorldBuilding 五维模型 |
| **工具/API** | @tool 装饰器注册，Agent 自动发现 | FastAPI router, 手写 endpoint | 工具即 API，API 即工具 |
| **前端 GUI** | PySide6 桌面 (app/) | Web UI (FastAPI + 原生 JS) | 共存，共享同一数据层 |
| **一键启动** | 一键启动.ps1 (Ollama 模式) | 无 | PowerSession 同时启动桌面+Web |

---

## 分阶段实施计划

### 阶段 A — 数据层统一

**目标**：统一两边的数据模型和存储格式，确保读写兼容。

1. 将 novel-agent 领域模型 (`domain/models/`) 导入天机的 `features/novel/models.py`
2. 升级 `features/novel/manager.py` 支持新模型字段（同时兼容旧数据）
3. 添加数据迁移脚本 `scripts/migrate_novel_data.py`
4. 统一存储路径到 `data/novels/`

**文件变更**：
- `天机/features/novel/` — 核心变更
- `data/novels/` — 数据文件（自动迁移）

### 阶段 B — Agent 工具增强

**目标**：将 novel-agent 所有后端逻辑搬运为天机 Agent 工具。

1. 导入增强后的 manager 到 `features/novel/tools.py`
2. 新增工具：写作辅助、章节续写、世界观一致性检查
3. novel-agent 路由逻辑迁移为 Agent 编排链

**文件变更**：
- `features/novel/tools.py` — 新增工具
- `features/novel/prompts.py` — 写作提示词模板

### 阶段 C — Web 前端集成

**目标**：将 novel-agent 的 Web UI 接入天机，与桌面 GUI 共存。

1. 保留 novel-agent 前端文件（在 `frontend/` 或 `web/`）
2. 写一个轻量 FastAPI web 入口 `web_server.py`，复用天机数据层
3. 修改 PowerSession 一键启动，同时拉起桌面 + Web

**文件变更**：
- `web_server.py` — 新文件，FastAPI web 入口
- `frontend/` — 前端静态文件
- `一键启动.ps1` — 增加 Web 模式选项

### 阶段 D — novel-agent 退役

**目标**：确认所有功能迁移完毕后，清理重复代码。

1. 确认所有 novel-agent 功能在天机中可用
2. novel-agent 目录保留为历史参考（不删除，仅标记）
3. 更新文档

### 阶段 E — 测试与验证

1. 冒烟测试：创建故事 → 添加角色 → 写章节 → 查看
2. 桌面 GUI 测试
3. Web UI 测试
4. Agent 对话创作测试

---

## 数据模型对齐

### 故事 (Story) 统一字段

```python
{
    "id": str,              # uuid hex[:12]
    "title": str,           # 故事标题
    "author": str,          # 作者（新增）
    "genre": str,           # 类型
    "description": str,     # 简介
    "outline": str,         # 大纲
    "tone": str,            # 风格基调（新增）
    "pov": str,             # 视角（新增）
    "target_audience": str, # 目标读者（新增）
    "status": str,          # 状态: draft/ongoing/completed（新增）
    "tags": list[str],      # 标签（新增）
    "world": {              # 世界观
        "name": str,
        "description": str,
        "rules": str,
        "background": str,
        "dimensions": [     # 五维扩展（新增）
            {"category": str, "name": str, "description": str,
             "rules": list, "entities": list, "relations": list}
        ]
    },
    "characters": [         # 人物列表
        {"id": str, "name": str, "role": str, "traits": str,
         "background": str, "appearance": str, "arc": str}
    ],
    "chapters": [           # 章节列表
        {"id": str, "title": str, "content": str, "word_count": int,
         "notes": str, "status": str, "order_index": int,
         "created_at": str, "updated_at": str}
    ],
    "created_at": str,
    "updated_at": str
}
```

### 兼容策略

- **读**：manager.get_story() 先尝试新格式，若字段缺失则补默认值
- **写**：始终写入完整新格式
- **迁移**：一次性脚本，对每个旧文件补充缺失字段

---

## 架构图（逻辑分层）

```
┌─────────────────────────────────────────────────────────┐
│                    用户交互层                              │
│  ┌──────────────┐          ┌──────────────────────────┐  │
│  │ PySide6 桌面 │          │  Web UI (FastAPI+JS)     │  │
│  │ (app/)       │          │  (frontend/)             │  │
│  └──────┬───────┘          └──────────┬───────────────┘  │
├─────────┼─────────────────────────────┼──────────────────┤
│         └──────────┬──────────────────┘                   │
│                    ▼                                      │
│           ┌────────────────┐                              │
│           │ 天机 Agent     │  ← LLM 编排层               │
│           │ (core/agent)   │                              │
│           └────────┬───────┘                              │
│                    ▼                                      │
│           ┌────────────────┐                              │
│           │ 工具层          │  ← @tool 注册              │
│           │ features/novel │                              │
│           │   /tools.py    │                              │
│           └────────┬───────┘                              │
├────────────────────┼──────────────────────────────────────┤
│                    ▼                                      │
│           ┌────────────────┐                              │
│           │ 领域模型 + CRUD │  ← 统一数据层              │
│           │ features/novel │                              │
│           │   /manager.py  │                              │
│           │   /models.py   │                              │
│           └────────┬───────┘                              │
│                    ▼                                      │
│           ┌────────────────┐                              │
│           │ data/novels/   │  ← JSON 文件存储            │
│           │ *.json         │                              │
│           └────────────────┘                              │
└───────────────────────────────────────────────────────────┘
```

---

## 实施顺序

```
阶段 A (数据层统一) ──→ 阶段 B (Agent工具增强) ──→ 阶段 C (Web前端集成)
     │                                                      │
     └────────────────── 阶段 E (测试验证) ──────────────────┘
                                 │
                           阶段 D (清理)

实际执行：A → B → C（并行E）→ D
```
