# novel-Agent

> 双项目单体仓库（Monorepo）：**天机**（通用自动化智能体） + **novel-agent**（AI 辅助小说创作引擎）

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)

---

## 项目一览

| 项目 | 说明 | 技术栈 |
|------|------|--------|
| **[天机](天机/README.md)** | 自动化智能体框架，支持多 LLM 后端、ReAct 推理循环、工具调用 | Python CLI、YAML 配置 |
| **novel-agent** | AI 辅助小说创作引擎，含故事大纲、章节生成、角色管理、世界观构建 | FastAPI + DDD + 前端 |

---

## 📦 项目结构

```
novel-Agent/
├── 天机/                        # 项目一：天机智能体
│   ├── __init__.py
│   ├── __main__.py
│   ├── config.py / config.yaml  # 配置层
│   ├── core/                    # 核心引擎
│   │   ├── agent.py             # Agent 主体（ReAct 循环）
│   │   ├── llm.py               # LLM 抽象层
│   │   └── tool_runner.py       # 工具执行器
│   ├── tools/                   # 内置工具
│   │   ├── web_search.py        # 联网搜索
│   │   ├── file_ops.py          # 文件操作
│   │   ├── execute_python.py    # Python 代码执行
│   │   ├── memory_tool.py       # 记忆管理
│   │   └── planning.py          # 规划工具
│   ├── utils/                   # 工具函数
│   └── README.md                # 天机详细文档
│
├── novel-agent/                 # 项目二：小说创作引擎
│   ├── domain/                  # 领域层（DDD）
│   │   ├── models/              # 领域模型
│   │   │   ├── story.py         # 故事
│   │   │   ├── chapter.py       # 章节
│   │   │   ├── character.py     # 角色
│   │   │   ├── worldbuilding.py # 世界观
│   │   │   ├── outline.py       # 大纲
│   │   │   └── knowledge_triple.py  # 知识三元组
│   │   ├── services/            # 领域服务
│   │   ├── repositories/        # 仓储接口
│   │   ├── events/              # 领域事件
│   │   └── value_objects/       # 值对象
│   ├── application/             # 应用层
│   │   ├── ai/                  # AI 服务
│   │   ├── engine/              # 创作引擎
│   │   ├── services/            # 应用服务
│   │   └── workflows/           # 工作流编排
│   ├── infrastructure/          # 基础设施层
│   ├── interfaces/              # 接口层（API）
│   ├── backend/                 # 后端服务
│   │   ├── main.py              # FastAPI 入口
│   │   ├── novel_agent.py       # Agent 实现
│   │   └── story_manager.py     # 故事管理器
│   ├── frontend/                # 前端界面
│   │   ├── index.html
│   │   ├── style.css
│   │   └── app.js
│   ├── tests/                   # 测试
│   └── requirements.txt
│
├── main.py                      # 天机 CLI 入口
├── requirements.txt             # 天机依赖
├── data/                        # 数据存储
├── memory.json                  # 记忆持久化
├── .gitignore
├── LICENSE                      # MIT 许可证
└── README.md                    # ← 本文件
```

---

## 🚀 快速开始

### 天机（通用智能体）

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

> 详细文档见 [天机/README.md](天机/README.md)

### novel-agent（小说创作引擎）

```bash
cd novel-agent

# 安装依赖
pip install -r requirements.txt

# 启动后端服务
cd backend && python main.py
```

前端为纯静态页面，直接打开 `frontend/index.html` 即可使用。

---

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源。
