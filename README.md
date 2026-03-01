## ToolMind 智能 Agent 平台

ToolMind 是一个面向「工具调用 + MCP + 多模型管理」场景打造的智能 Agent 平台。  
它以 FastAPI 为后端、Vue3 为前端，集成大语言模型、外部工具、MCP 服务器和多种知识处理能力，支持复杂任务分解、自动规划和流式对话。

---

## 目录

- [项目简介](#项目简介)
- [核心功能与特性](#核心功能与特性)
- [系统架构与项目结构](#系统架构与项目结构)
- [快速开始](#快速开始)
- [核心概念说明](#核心概念说明)
- [联网搜索与外部工具](#联网搜索与外部工具)
- [部署与运维建议](#部署与运维建议)
- [文档与 API](#文档与-api)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

---

## 项目简介

**ToolMind** 旨在为开发者和团队提供一个可扩展的「智能体工作台」：

- **统一接入多种大模型**：自建模型管理能力，支持自行配置模型名称、API Key、Base URL、提供商等。
- **多种智能体形态**：
  - 面向对话和工具调用的 **StreamingAgent**（流式对话 Agent）
  - 面向复杂任务分解与执行编排的 **MindAgent**（任务规划 Agent）
- **强大的工具生态**：内置联网搜索工具，支持将 MCP 服务器暴露为工具，形成统一的工具调用面板。
- **现代化前端控制台**：通过 Web 界面管理模型、Agent、MCP 服务器、工具与会话。

---

## 核心功能与特性

### 智能体系统（Agents）

- **StreamingAgent**（`backend/toolmind/services/mind/agent.py`）
  - 基于 LangGraph / LangChain 构建的 ReAct 风格 Agent。
  - 支持流式输出，对话过程可以持续推送增量内容。
  - 通过中间件自动选择工具（LLMToolSelectorMiddleware），减少手工配置负担。
  - 集成使用统计回调，可记录 Token 用量等元数据。

- **MindAgent**（`backend/toolmind/services/mind/agent.py`）
  - 支持从自然语言问题出发，自动生成 **任务图（Task Graph）**：
    - 拆分为多个步骤（`MindTaskStep`），构建前后依赖关系。
    - 每一步可绑定不同工具（包括 MCP 工具和内置工具）。
  - 执行过程中：
    - 逐步调用工具，实时产出中间结果事件（便于前端实时展示步骤进度）。
    - 最后对整体结果进行自我评估（评分 + 原因），不满足阈值时可自动重跑若干次。
  - 将问题、任务图、步骤结果和最终回答写入工作区会话，便于后续回顾与追踪。

### 工具与插件体系

- **统一工具抽象**
  - 内置工具（如 `web_search`）通过 `langchain.tools.tool` 进行封装。
  - MCP 工具通过 `MCPManager` 动态加载并适配为统一的工具描述。
  - 所有工具都可被模型以「函数调用」方式自动触发。

- **工具发现与选择**
  - 当工具数量较多时，可先通过「搜索工具」这种元工具（`search_available_tools`）搜索相关工具，再按需激活，减少上下文负担。
  - MindAgent 会根据任务步骤自动选择合适工具并注入执行参数。

### MCP 集成能力

- 支持通过 MCP 协议接入外部服务：
  - 在配置中维护 MCP 服务器列表。
  - 通过 `MCPManager` 统一管理连接、工具枚举等。
  - 将 MCP 工具转换为标准的「可调用工具」，用于 MindAgent 的任务执行。
- 每个 MCP 工具与其所属 MCP 服务器之间建立映射关系，便于在调用时附加用户级配置（API Key 等）。

### 多模型管理与调用策略

- **多模型配置**（`backend/toolmind/schema/common.py` 中的 `MultiModels`）
  - 支持对不同用途的模型进行拆分配置，例如：
    - `conversation_model`：对话与内容生成
    - `tool_call_model`：工具调用与意图识别
    - `reasoning_model`：复杂推理
    - `embedding` / `rerank` 等
  - 同时保留扩展字段能力（`extra="allow"`），便于后续扩展其他模型角色。

- **运行时模型选择**
  - 通过 `ModelManager` 封装：
    - 按用户 ID 选择对话模型 / 意图识别模型。
    - MindAgent、StreamingAgent 根据场景选择不同模型实例。
  - 某些流程绑定 `response_format={"type": "json_object"}` 来强约束输出结构，配合 JSON 修复逻辑提升鲁棒性。

### 前端控制台与交互体验

- 使用 Vue3 + TypeScript + Vite + Element Plus 构建。
- 提供：
  - Agent 管理、MCP 服务器管理、模型配置、会话记录等页面。
  - 对话界面支持展示流式内容、步骤执行结果、任务图等。

---

## 系统架构与项目结构

### 整体架构

- **前端应用**（`frontend/`）：管理界面与对话界面。
- **后端服务**（`backend/toolmind/`）：
  - `api/`：FastAPI 路由与接口层。
  - `core/`：模型管理、Agent 核心实现等。
  - `services/`：业务服务，包括：
    - `mind/`：MindAgent、StreamingAgent 等智能体服务。
    - `web_search/`：统一联网搜索工具实现。
    - 其他如 `rag/`、`deepsearch/`、`transform_paper/`、`rewrite/` 等扩展服务。
  - `schema/`：Pydantic 数据模型（请求/响应、内部结构）。
  - `prompts/`：提示词模板（如任务生成、结果评估等）。
- **配置与部署**：
  - `backend/toolmind/config.yaml`：服务端主要运行配置。
  - `requirements.txt`：后端依赖。
  - 前端 `package.json` / `vite.config.ts` 等构建配置。

### 目录示意（简化）

```
toolmind/
├── README.md
├── requirements.txt
├── backend/
│   └── toolmind/
│       ├── main.py                  # FastAPI 入口
│       ├── config.yaml              # 服务与模型等配置
│       ├── api/                     # API 层
│       ├── core/                    # 核心模型与 Agent 能力
│       ├── services/
│       │   ├── mind/                # MindAgent、StreamingAgent
│       │   ├── web_search/         # Tavily 联网搜索工具
│       │   └── ...                  # 其他业务服务
│       ├── schema/                  # Pydantic 模型
│       ├── prompts/                 # 提示词模板
│       └── utils/                   # 工具函数
└── frontend/                        # 前端应用
    ├── src/
    │   ├── pages/                   # 页面组件（对话、Agent、配置等）
    │   ├── components/
    │   ├── router/
    │   └── store/
    └── vite.config.ts
```

---

## 快速开始

### 环境要求

- **Python**：推荐 3.10 及以上
- **Node.js**：推荐 18 及以上
- **数据库**：MySQL / Redis（如需持久化和缓存）
- **可选组件**：
  - 向量数据库（ChromaDB / Milvus）
  - Elasticsearch（如需全文检索）
  - Docker / Docker Compose（用于容器化部署）

### 1. 克隆仓库并安装依赖

```bash
# 克隆项目
git clone https://github.com/hhgzeng/toolmind.git
cd toolmind

# 安装后端依赖
pip install -r requirements.txt
```

前端依赖安装：

```bash
cd frontend
npm install
```

### 2. 配置后端（`backend/toolmind/config.yaml`）

根据实际环境修改配置文件，主要包括：

- **服务基本信息**（`server`）：`host` / `port` / `project_name`
- **数据库配置**（`mysql`）：`endpoint`、`async_endpoint`
- **Redis 配置**（`redis`）：`endpoint`
- **多模型配置**（`multi_models`）：`conversation_model`、`tool_call_model` 等
- **工具配置**（`tools`）：如 Tavily API Key（用于 `web_search` 工具）
- **对象存储 / 资源配置**（`aliyun_oss` / `default_config`）：按需配置

> 生产环境请务必通过环境变量或安全配置方式注入敏感信息，不要直接提交到版本库。

### 3. 启动后端服务

```bash
cd backend
python -m toolmind.main
```

默认访问地址（以配置为准）：

- API 服务：`http://127.0.0.1:7860`
- API 文档（Swagger）：`http://127.0.0.1:7860/docs`

### 4. 启动前端开发服务器

```bash
cd frontend
npm run dev
```

默认前端访问地址：

- 前端界面：`http://localhost:8090`

---

## 核心概念说明

### 模型配置（MultiModels）

对应 `backend/toolmind/schema/common.py`：

- **`ModelConfig`**：`model_name`、`api_key`、`base_url`
- **`MultiModels`**：预定义了多种角色模型字段（如 `conversation_model`、`tool_call_model` 等），支持 `extra="allow"` 扩展。

后端在运行时通过 `ModelManager` 读取这些配置并实例化对应模型对象。

### Mind 智能体（MindAgent）

核心数据结构位于 `backend/toolmind/schema/mind.py`：

- **`MindGuidePrompt` / `MindGuidePromptFeedBack`**：用于生成引导提示词，支持反馈迭代。
- **`MindTask`**：描述一个完整任务（`query`、`guide_prompt`、`web_search`、`plugins`、`mcp_servers`）。
- **`MindTaskStep`**：单个任务步骤（`step_id`、`title`、`target`、`workflow`、`input`、`result` 等）。

执行流程由 `MindAgent.submit_mind_task` 负责：生成任务图 → 按步骤调用工具 → 汇总结果 → 自我评估 → 可选重跑 → 写入工作区会话。

### StreamingAgent 与工具中间件

`backend/toolmind/services/mind/agent.py` 中的 `StreamingAgent`：

- 初始化过程：加载 MCP 工具、本地工具（如 `tavily_search`）、对话模型与工具调用模型，创建 ReAct Agent。
- 中间件（`EmitEventAgentMiddleware`）：在工具调用前后抛出自定义事件（`START` / `END` / `ERROR`），便于前端展示工具执行状态。
- 流式接口（`astream`）：通过 LangGraph 的 `astream` 实现 token 级别流式输出，并推送工具执行事件与模型回复片段。

### 工具收集与暴露（_obtain_mind_tools）

`MindAgent._obtain_mind_tools` 负责综合可用工具：

- 当 `enable_web_search` 为 True 时，将 `web_search` 工具作为 OpenAI 风格工具暴露。
- 从 MCP 服务器中加载工具，为每个 MCP 工具构造统一的参数 Schema，并记录工具与 MCP 服务器 ID 的映射。

---

## 联网搜索与外部工具

### Tavily 联网搜索（web_search）

`backend/toolmind/services/web_search/action.py` 中定义了统一的联网搜索工具：

- 工具名称：`web_search`
- 封装库：`tavily-python`
- 主要参数：`query`、`topic`、`max_results`、`time_range`

Agent 在需要外部信息时会自动调用该工具，并将搜索结果拼接成可阅读文本返回给模型。

> 使用前请在 `config.yaml` 中配置 Tavily 的 API Key。

---

## 部署与运维建议

- **配置管理**：建议使用环境变量或独立配置中心注入敏感信息；`config.yaml` 可作为默认模板。
- **日志与监控**：后端基于 `loguru` 输出日志，可接入集中式日志系统；可在 Agent 中增加 Callbacks 收集 Token 用量、错误情况等。
- **容器化部署**：建议为后端和前端分别构建镜像，通过 Docker Compose 或 K8s 编排；数据库与 Redis 建议使用托管服务或独立容器。

---

## 文档与 API

- **在线 API 文档**：启动后端服务后访问 `/docs`（Swagger UI）
- **项目内部文档**：如存在 `docs/toolmind.md`、`docs/api.md` 等，可参考获取更详细的接口说明
- **前端调试指南**：`frontend/DEBUGGING_GUIDE.md`

---

## 贡献指南

欢迎提交 Issue、Pull Request 或任何形式的反馈与改进建议：

- **Bug 修复**：提交尽可能详细的复现步骤与期望行为
- **新功能**：先通过 Issue 或讨论区描述需求场景与设计思路
- **文档完善**：补充使用示例、配置说明、多语言文档等
- **生态扩展**：新增 MCP 服务器适配、新工具、新 Agent 模式等

---

## 许可证

本项目采用 **MIT License** 开源许可证。  
你可以自由地使用、修改和分发本项目，但需要保留原始版权和许可声明。
