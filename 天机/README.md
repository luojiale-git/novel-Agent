# 天机 — 自动化智能体框架

> **"天机"** 取意"天机不可泄露"中的玄妙与智能，是一个轻量级、可扩展的自动化智能体框架，支持多 LLM 后端接入与丰富的工具调用能力。

---

## 目录

- [核心特性](#核心特性)
- [快速开始](#快速开始)
- [使用指南](#使用指南)
- [配置说明](#配置说明)
- [工具集](#工具集)
- [项目结构](#项目结构)
- [技术栈](#技术栈)
- [许可证](#许可证)

---

## 核心特性

### 🔌 多 LLM 后端支持
通过统一的 LLM 抽象层，可无缝切换：
- **DeepSeek Chat / Reasoner** — 默认后端，支持联网搜索
- **OpenAI Compatible** — 兼容任何 OpenAI 格式的 API（如 vLLM、LM Studio 等）
- **Ollama** — 本地部署，完全离线，数据隐私无忧

### 🔄 ReAct 智能循环
采用 **ReAct（推理+行动）** 模式驱动智能体：
1. 接收用户输入
2. 推理下一步行动
3. 调用工具获取结果
4. 整合思考后回复用户
5. 支持最多 40 步深度推理循环

### 🧰 五大内置工具

| 工具 | 能力 |
|------|------|
| **文件操作** | 读写文件、目录浏览、glob 匹配 |
| **代码搜索** | 基于正则的代码内容检索 |
| **命令执行** | 安全受限的 Shell 命令执行 |
| **网络搜索** | 实时网页信息检索 |
| **API 调用** | 通用 HTTP REST API 客户端 |

### 🛡️ 安全机制
- **命令白名单** — 仅允许执行预设命令
- **超时控制** — 防止长时间阻塞
- **输出截断** — 避免上下文溢出
- **文件路径校验** — 防止目录遍历攻击
- **YAML 配置泄敏** — `config.yaml` 默认被 `.gitignore` 排除

### 🧠 对话记忆管理
- 滑动窗口机制，保留最近 N 轮对话
- 系统提示词保护（永远不被修剪）
- 可选的 JSON 文件持久化
- 一键清空记忆

### 📖 StoryCraft 叙事引擎（实验性）
内置故事生成子模块，包含：
- 中式玄幻、赛博朋克等世界观模板
- 叙事结构框架（三幕式、英雄之旅等）
- 人物设定与情节生成器

---

## 快速开始

### 环境要求

- **Python 3.10+**
- 至少一个 LLM 后端的 API Key（DeepSeek / OpenAI）或本地模型（Ollama）

### 安装

```bash
# 克隆仓库
git clone <your-repo-url>
cd 天机

# 安装依赖
pip install -r requirements.txt
```

### Windows 快速部署（推荐）

以管理员身份运行 PowerShell：

```powershell
# 一键部署（安装 Ollama + 拉取模型 + 安装依赖）
.\一键启动.ps1
```

或分步执行：

```powershell
# 1. 创建模型目录
New-Item -ItemType Directory -Path "D:\ollama\models" -Force

# 2. 设置 Ollama 模型存储路径
[Environment]::SetEnvironmentVariable("OLLAMA_MODELS", "D:\ollama\models", "User")

# 3. 安装 Ollama（如果未安装）
#    从 https://ollama.com 下载安装

# 4. 拉取模型
ollama pull qwen2:7b

# 5. 安装依赖
pip install -r requirements.txt
```

### 配置

复制配置文件并填写：

```bash
# 创建配置文件（从模板）
cp config.example.yaml config.yaml
# 注意：config.yaml 已被 .gitignore 排除，不会提交到仓库
```

编辑 `config.yaml`，至少配置一个 LLM 后端：

```yaml
llm:
  provider: deepseek    # 可选: deepseek, openai, ollama
  model: deepseek-chat

deepseek:
  api_key: "sk-your-key-here"    # 替换为你的 API Key
  api_base: "https://api.deepseek.com"
```

### 运行

```bash
python main.py
```

进入交互式 REPL 后，直接输入问题即可：

```
╔══════════════════════════════════════════╗
║           天机 · 自动化智能体              ║
║         输入 /help 查看帮助               ║
║         输入 /exit 或 Ctrl+C 退出          ║
╚══════════════════════════════════════════╝

>>> 帮我搜索今天的科技新闻
```

---

## 使用指南

### REPL 模式（默认）

启动后进入交互式命令行，支持：

| 命令 | 功能 |
|------|------|
| `/help` | 显示帮助信息 |
| `/exit` | 退出程序 |
| `/clear` | 清空对话记忆 |
| `/tools` | 查看可用工具列表 |
| `/config` | 查看当前配置 |
| `/history` | 显示最近对话历史 |

### 单次查询模式

```bash
python main.py "你的问题"
```

执行单次查询后自动退出，适合脚本调用。

### 示例

```
>>> 读取当前目录下的 main.py 文件，告诉我它的主要功能
>>> 搜索我电脑上 Python 相关的文件
>>> 帮我查一下 DeepSeek 最新的 API 文档
>>> 写一个简单的 HTTP 服务器
```

---

## 配置说明

配置通过 `config.yaml` 管理，支持 YAML + 环境变量覆盖。

### 完整配置项

```yaml
# LLM 后端配置
llm:
  provider: deepseek          # deepseek | openai | ollama
  model: deepseek-chat        # 模型名称
  temperature: 0.7            # 采样温度 (0-2)
  max_tokens: 4096            # 最大输出 token 数

# DeepSeek 配置
deepseek:
  api_key: ""                 # API Key
  api_base: "https://api.deepseek.com"

# OpenAI 兼容配置
openai:
  api_key: ""                 # API Key
  api_base: ""                # 兼容接口地址

# Ollama 配置
ollama:
  api_base: "http://localhost:11434"
  model: "qwen2:7b"

# 智能体配置
agent:
  max_iterations: 40          # 最大推理循环步数
  verbose: true               # 是否显示详细推理过程

# 命令执行安全配置
allowed_commands:
  - python
  - pip
  - git
  - node
  - npm
  - npx
  - cargo
  - ls
  - dir
  - pwd
  - cat
  - type
  - echo
  - mkdir
  - curl
  - wget

command_timeout: 120          # 命令超时时间（秒）

# 记忆管理
memory_max_turns: 20          # 保留最近 N 轮对话
memory_persistent: true       # 是否持久化记忆
memory_storage_path: "data/memory.json"

# 日志
log_level: "INFO"             # DEBUG | INFO | WARNING | ERROR
```

### 环境变量覆盖（可选）

```bash
# 可以通过环境变量覆盖敏感配置
export DEEPSEEK_API_KEY="sk-your-key"
export OPENAI_API_KEY="sk-your-key"

# 程序会优先读取环境变量
```

---

## 工具集

智能体通过以下工具与外界交互，所有工具均有完整的中文日志输出，便于调试。

### 1. 文件操作工具 (`FileTools`)
- `read(path)` — 读取文件内容
- `write(path, content)` — 写入/创建文件
- `edit(path, old, new)` — 精确文本替换编辑
- `glob(pattern)` — 按通配符搜索文件
- `ls(path)` — 列出目录内容

### 2. 代码搜索工具 (`CodeSearchTools`)
- `search(pattern, path, include)` — 正则搜索代码内容
- 支持文件类型过滤（如 `*.py`, `*.{ts,tsx}`）

### 3. 命令执行工具 (`ShellTools`)
- `execute(command, workdir, timeout, description)` — 安全执行命令
- `execute_async(command)` — 异步提交后台任务
- `get_system_info()` — 系统信息查询
- 支持白名单校验和输出截断

### 4. 网络搜索工具 (`WebSearchTools`)
- `search(query, num_results)` — 实时网页搜索
- `fetch(url)` — 获取网页内容

### 5. API 调用工具 (`APITools`)
- `call_api(method, url, headers, params, json_data)` — 通用 HTTP 客户端
- 自动格式化 JSON 响应

---

## 项目结构

```
天机/
├── main.py                    # 入口文件（CLI + REPL）
├── config.py                  # 配置管理器（YAML + 环境变量）
├── config.example.yaml        # 配置模板（不含密钥）
├── requirements.txt           # Python 依赖
├── setup.ps1                  # 部署脚本
├── 一键启动.ps1               # Windows 一键启动（Ollama 模式）
├── README.md                  # 本文件
│
├── core/                      # 核心模块
│   ├── __init__.py
│   ├── agent.py               # ReAct 智能体主循环
│   ├── llm.py                 # LLM 抽象层
│   ├── memory.py              # 对话记忆管理器
│   └── tool_registry.py       # 工具注册中心
│
├── tools/                     # 工具模块
│   ├── __init__.py
│   ├── file_tools.py          # 文件操作工具
│   ├── code_search.py         # 代码搜索工具
│   ├── shell_tools.py         # 命令执行工具
│   ├── web_search.py          # 网络搜索工具
│   └── api_tools.py           # API 调用工具
│
├── storycraft/                # 叙事引擎（实验性）
│   ├── __init__.py
│   ├── engine.py              # 叙事引擎主模块
│   ├── templates.py           # 世界观模板
│   └── world_view.py          # 世界观配置
│
├── utils/                     # 工具函数
│   ├── __init__.py
│   └── helpers.py             # 辅助函数（日志、格式化）
│
├── data/                      # 运行时数据目录
│   └── memory.json            # 持久化记忆文件（自动生成）
│
└── tools_data/                # 工具临时数据
    └── *.txt                  # 临时搜索结果等
```

---

## 技术栈

| 组件 | 技术 |
|------|------|
| **语言** | Python 3.10+ |
| **LLM 接口** | DeepSeek API / OpenAI API / Ollama REST API |
| **HTTP 请求** | `requests` |
| **配置管理** | `pyyaml` + 环境变量 |
| **数据持久化** | JSON 文件存储 |
| **命令行交互** | 原生 `input()` REPL |

### 依赖清单

```
requests>=2.28.0
pyyaml>=6.0
```

极简依赖，开箱即用。

---

## 开发计划

- [x] 多 LLM 后端支持（DeepSeek / OpenAI / Ollama）
- [x] ReAct 推理循环
- [x] 五工具集
- [x] 对话记忆管理
- [x] 安全沙箱（命令白名单）
- [x] 配置管理（YAML + 环境变量）
- [ ] 工具调用结果的流式输出
- [ ] 插件系统（动态加载自定义工具）
- [ ] Web UI 界面
- [ ] 多智能体协作
- [ ] 更多 LLM 后端（Anthropic, Google Gemini 等）
- [ ] Docker 部署支持

---

## 许可证

本项目基于 MIT 许可证开源。

---

*"天机不可泄露，但智能触手可及。"*
