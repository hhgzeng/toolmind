## 📋 目录

- [🎯 项目简介](#-项目简介)
- [✨ 功能展示](#-功能展示)
- [🚨 重要版本说明](#-重要版本说明)
- [💡 功能特性](#-功能特性)
- [🛠 技术栈](#-技术栈)
- [📁 项目结构](#-项目结构)
- [🚀 快速开始](#-快速开始)
- [📦 部署](#-高级部署指南)
- [📖 文档](#-文档)
- [📄 许可证](#-许可证)

---

## 🎯 项目简介

ToolMind 是一个现代化的智能对话系统，基于大语言模型构建，提供了丰富的AI对话功能。系统采用前后端分离架构，支持多种AI模型、知识库检索、工具调用、MCP服务器集成等高级功能。

### 🌟 核心亮点

- 🤖 **多模型支持**: 集成OpenAI、DeepSeek、Qwen等主流大语言模型
- 🧠 **智能Agent**: 支持多Agent协作，具备推理和决策能力
- 🌐 **MCP集成**: 支持Model Context Protocol服务器
- 💬 **实时对话**: 流式响应，提供流畅的对话体验
- 🎨 **现代界面**: 基于Vue 3和Element Plus的美观UI

---

## ✨ 功能展示


### 🌟 智能Agent功能演示

### 🔁智能体工具多轮调用


## 💡 功能特性

### 🎯 核心功能模块

#### 🧠 **智能Agent系统**
> *多智能体协作，自动化任务执行*

- 🤝 **多Agent协作**: 智能体间任务分工与协调
- 🔧 **任务自动化**: 智能分解复杂任务，自动执行
- ⚙️ **能力配置**: 灵活的Agent能力定义和管理
- 🔄 **工作流编排**: 可视化工作流设计和执行
- 📊 **执行监控**: 实时监控Agent执行状态
- 🎯 **目标导向**: 基于目标的智能决策和行动


#### 🛠️ **丰富工具生态**

### 🔧 **高级特性**

</div>

<table>
<tr>
<td width="33%">

#### 🌐 **MCP服务器**
*Model Context Protocol集成*

- 🔌 **协议支持**: 完整MCP协议实现
- 🏗️ **自定义服务**: 支持用户自定义MCP服务器
- 🔄 **动态加载**: 运行时动态加载MCP服务
- ⚡ **高性能**: 异步处理，快速响应

</td>
<td width="33%">

#### 👤 **用户管理**
*安全的身份认证与权限控制*

- 🔐 **安全认证**: JWT令牌，安全可靠
- 👥 **用户系统**: 注册、登录、个人资料
- 🛡️ **权限控制**: 细粒度权限管理
- ⚙️ **个性配置**: 个人偏好设置
- 📊 **使用统计**: 用户行为分析

</td>
<td width="33%">

#### 🏗️ **系统架构**
*现代化的技术架构*

- 🔄 **前后端分离**: Vue3 + FastAPI
- 📡 **实时通信**: WebSocket支持
- 💾 **多数据库**: MySQL、Redis、ChromaDB
- 🐳 **容器化**: Docker部署，易于扩展
- 📈 **可监控**: 完整的日志和监控体系

</td>
</tr>
</table>

### 🎨 **技术亮点**

<div align="center">

| 🌟 **特性** | 📝 **描述** | 🔧 **技术** |
|:---:|:---|:---|
| **流式响应** | 实时生成内容，提升用户体验 | Server-Sent Events |
| **向量检索** | 语义级别的知识检索 | ChromaDB + Embedding |
| **异步处理** | 高并发任务处理 | FastAPI + AsyncIO |
| **模块化设计** | 松耦合架构，易于扩展 | 微服务架构 |
| **智能缓存** | Redis缓存，提升响应速度 | Redis + 智能缓存策略 |

</div>

---

## 🛠 技术栈

### 后端技术
- **框架**: FastAPI (Python 3.13+)
- **AI集成**: LangChain, OpenAI, Anthropic
- **数据库**: MySQL 8.0, Redis 7.0
- **向量数据库**: ChromaDB, Milvus
- **搜索引擎**: Elasticsearch
- **文档处理**: PyMuPDF, Unstructured
- **异步任务**: Celery
- **部署**: Gunicorn, Uvicorn

### 前端技术
- **框架**: Vue 3.4+ (Composition API)
- **UI组件**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **构建工具**: Vite 5
- **开发语言**: TypeScript
- **样式**: SCSS
- **Markdown**: md-editor-v3

### 开发工具
- **包管理**: Poetry (后端), npm (前端)
- **代码格式**: Black, Prettier
- **类型检查**: mypy, TypeScript
- **容器化**: Docker, Docker Compose

---

## 📁 项目结构

> 🏗️ **完整的项目架构** - 模块化设计，清晰的职责分离

<details>
<summary><b>🔍 点击展开完整项目结构</b></summary>

```
AgentChat/                          # 🏠 项目根目录
├── 📄 README.md                   # 📖 项目说明文档
├── 📄 LICENSE                     # ⚖️ 开源许可证
├── 📄 .gitignore                  # 🚫 Git忽略文件配置
├── 📄 pyproject.toml              # 🐍 Python项目配置
├── 📄 requirements.txt            # 📦 Python依赖包列表
│
├── 📁 .vscode/                    # 🔧 VSCode编辑器配置
├── 📁 .idea/                      # 💡 JetBrains IDE配置
│
├── 📁 docs/                       # 📚 项目文档目录
│   ├── 📄 API_Documentation_v3.0.md  # 🔄 最新API文档
│   ├── 📄 API_Documentation_v2.0.md  # 📋 v2.0 API文档
│   └── 📄 API_Documentation_v1.0.md  # 📝 v1.0 API文档
│
├── 📁 docker/                     # 🐳 容器化配置
│   ├── 📄 Dockerfile              # 🐳 Docker镜像构建文件
│   └── 📄 docker-compose.yml      # 🔧 Docker编排配置
│
└── 📁 src/                        # 💻 源代码目录
    ├── 📁 backend/                # 🔧 后端服务
    │   ├── 📁 chroma_db/          # 🗄️ ChromaDB向量数据库
    │   └── 📁 agentchat/          # 🤖 核心后端应用
    │       ├── 📄 __init__.py     # 🐍 Python包初始化文件
    │       ├── 📄 main.py         # 🚀 FastAPI应用入口
    │       ├── 📄 settings.py     # ⚙️ 应用配置设置
    │       ├── 📄 config.yaml     # 📋 YAML配置文件
    │       │
    │       ├── 📁 api/            # 🌐 API路由层
    │       │   ├── 📄 __init__.py
    │       │   ├── 📄 router.py   # 🔀 主路由配置
    │       │   ├── 📄 JWT.py      # 🔐 JWT认证处理
    │       │   ├── 📁 v1/         # 📊 v1版本API接口
    │       │   ├── 📁 services/   # 🔧 服务层API
    │       │   └── 📁 errcode/    # ❌ 错误码定义
    │       │
    │       ├── 📁 core/           # 🏗️ 核心功能模块
    │       │   ├── 📄 __init__.py
    │       │   └── 📁 models/     # 🧠 AI模型管理
    │       │
    │       ├── 📁 database/       # 🗃️ 数据库层
    │       │   ├── 📄 __init__.py # 🔗 数据库连接配置
    │       │   ├── 📄 init_data.py # 🏗️ 数据库初始化脚本
    │       │   ├── 📁 models/     # 📊 数据模型定义
    │       │   └── 📁 dao/        # 💾 数据访问对象
    │       │
    │       ├── 📁 services/       # 🎯 业务服务层
    │       │   ├── 📄 __init__.py
    │       │   ├── 📄 retrieval.py      # 🔍 信息检索服务
    │       │   ├── 📄 rag_handler.py    # 📚 RAG处理服务
    │       │   ├── 📄 aliyun_oss.py     # ☁️ 阿里云OSS服务
    │       │   ├── 📄 redis.py          # 💾 Redis缓存服务
    │       │   ├── 📁 rag/              # 📖 RAG检索增强生成
    │       │   ├── 📁 mars/             # 🚀 Mars智能体服务
    │       │   ├── 📁 mcp/              # 🔌 MCP协议服务
    │       │   ├── 📁 mcp_agent/        # 🤖 MCP Agent服务
    │       │   ├── 📁 mcp_openai/       # 🧠 MCP OpenAI集成
    │       │   ├── 📁 deepsearch/       # 🕵️ 深度搜索服务
    │       │   ├── 📁 transform_paper/  # 📄 论文转换服务
    │       │   ├── 📁 autobuild/        # 🏗️ 自动构建服务
    │       │   └── 📁 rewrite/          # ✏️ 内容重写服务
    │       │
    │       ├── 📁 tools/          # 🛠️ 工具集成
    │       │   ├── 📄 __init__.py # 🧰 工具注册和管理
    │       │   ├── 📁 arxiv/      # 📚 ArXiv论文工具
    │       │   ├── 📁 delivery/   # 📦 快递查询工具
    │       │   ├── 📁 web_search/ # 🔍 网络搜索工具
    │       │   ├── 📁 get_weather/     # 🌤️ 天气查询工具
    │       │   ├── 📁 send_email/      # 📧 邮件发送工具
    │       │   ├── 📁 text2image/      # 🎨 文本转图片工具
    │       │   ├── 📁 image2text/      # 👁️ 图片转文本工具
    │       │   ├── 📁 convert_to_pdf/  # 📄 PDF转换工具
    │       │   ├── 📁 convert_to_docx/ # 📝 Word转换工具
    │       │   ├── 📁 resume_optimizer/# 📋 简历优化工具
    │       │   ├── 📁 rag_data/        # 📊 RAG数据处理工具
    │       │   └── 📁 crawl_web/       # 🕷️ 网页爬虫工具
    │       │
    │       ├── 📁 prompts/        # 💬 提示词模板库
    │       ├── 📁 config/         # ⚙️ 配置文件目录
    │       ├── 📁 schema/         # 📋 数据模式定义
    │       ├── 📁 data/           # 💾 数据存储目录
    │       ├── 📁 utils/          # 🧰 通用工具函数
    │       └── 📁 test/           # 🧪 测试代码目录
    │
    └── 📁 frontend/               # 🎨 前端应用
        ├── 📄 package.json       # 📦 Node.js项目配置
        ├── 📄 package-lock.json  # 🔒 依赖版本锁定
        ├── 📄 tsconfig.json      # 🔧 TypeScript配置
        ├── 📄 tsconfig.app.json  # 📱 应用TypeScript配置
        ├── 📄 tsconfig.node.json # 🔧 Node环境TypeScript配置
        ├── 📄 vite.config.ts     # ⚡ Vite构建配置
        ├── 📄 index.html         # 🌐 HTML入口文件
        ├── 📄 .gitignore         # 🚫 前端Git忽略配置
        ├── 📄 README.md          # 📖 前端说明文档
        ├── 📄 DEBUGGING_GUIDE.md # 🐛 调试指南
        ├── 📄 auto-imports.d.ts  # 🔄 自动导入类型声明
        ├── 📄 components.d.ts    # 🧩 组件类型声明
        │
        ├── 📁 public/            # 🌍 静态资源目录
        │
        └── 📁 src/               # 💻 前端源代码
            ├── 📄 main.ts        # 🚀 Vue应用入口
            ├── 📄 App.vue        # 🏠 根组件
            ├── 📄 style.css      # 🎨 全局样式
            ├── 📄 type.ts        # 📋 TypeScript类型定义
            ├── 📄 vite-env.d.ts  # 🔧 Vite环境类型声明
            │
            ├── 📁 components/    # 🧩 可复用组件库
            │   ├── 📁 agentCard/      # 🤖 Agent卡片组件
            │   ├── 📁 commonCard/     # 🃏 通用卡片组件
            │   ├── 📁 dialog/         # 💬 对话框组件
            │   ├── 📁 drawer/         # 📜 抽屉组件
            │   └── 📁 historyCard/    # 📜 历史记录卡片
            │
            ├── 📁 pages/         # 📄 页面组件
            │   ├── 📄 index.vue       # 🏠 首页
            │   ├── 📁 agent/          # 🤖 Agent管理页面
            │   ├── 📁 configuration/ # ⚙️ 配置页面
            │   ├── 📁 construct/      # 🏗️ 构建页面
            │   ├── 📁 conversation/   # 💬 对话页面
            │   ├── 📁 homepage/       # 🏠 主页模块
            │   ├── 📁 knowledge/      # 📚 知识库页面
            │   ├── 📁 login/          # 🔐 登录页面
            │   ├── 📁 mars/           # 🚀 Mars对话页面
            │   ├── 📁 mcp-server/     # 🖥️ MCP服务器页面
            │   ├── 📁 model/          # 🧠 模型管理页面
            │   ├── 📁 notFound/       # ❓ 404页面
            │   ├── 📁 profile/        # 👤 用户资料页面
            │   └── 📁 tool/           # 🛠️ 工具管理页面
            │
            ├── 📁 router/        # 🛣️ 路由配置
            ├── 📁 store/         # 🗄️ 状态管理(Pinia)
            ├── 📁 apis/          # 🌐 API接口定义
            ├── 📁 utils/         # 🧰 工具函数库
            └── 📁 assets/        # 🖼️ 静态资源(图片、字体等)
```

</details>

### 📊 项目统计

<div align="center">

| 📂 **类别** | 📈 **数量** | 📝 **说明** |
|:---:|:---:|:---|
| **后端模块** | 15+ | API、服务、工具、数据库等核心模块 |
| **前端页面** | 12+ | 完整的用户界面和交互页面 |
| **内置工具** | 10+ | 涵盖搜索、文档、图像、通信等功能 |
| **AI模型** | 5+ | 支持主流大语言模型和嵌入模型 |
| **MCP服务** | 多个 | 可扩展的MCP协议服务器 |

</div>

### 📊 代码量统计

<div align="center">

*📝 基于文件扩展名的详细代码统计*

| 🔍 **文件类型** | 📁 **文件数量** | 📄 **总行数** | 📉 **最少行数** | 📈 **最多行数** | 📊 **平均行数** |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **🐍 Python** | 247 | 19,599 | 0 | 1,039 | 79 |
| **🎨 Vue** | 31 | 21,907 | 12 | 2,588 | 706 |
| **📰 Markdown** | 8 | 3,475 | 5 | 1,079 | 434 |
| **⚡ TypeScript** | 46 | 2,103 | 1 | 212 | 45 |
| **📋 TXT** | 1 | 539 | 539 | 539 | 539 |
| **📦 JSON** | 11 | 348 | 7 | 110 | 31 |
| **⚙️ TOML** | 1 | 328 | 328 | 328 | 328 |
| **🎨 CSS** | 1 | 176 | 176 | 176 | 176 |
| **🔧 YML** | 2 | 177 | 52 | 125 | 88 |
| **📋 YAML** | 2 | 152 | 35 | 117 | 76 |
| **⚙️ CONF** | 1 | 101 | 101 | 101 | 101 |
| **🚀 Shell** | 2 | 87 | 35 | 52 | 43 |
| **🚦 PROD** | 1 | 41 | 41 | 41 | 41 |
| **🚫 GitIgnore** | 1 | 24 | 24 | 24 | 24 |
| **🌐 HTML** | 1 | 13 | 13 | 13 | 13 |
| **🐳 DockerIgnore** | 1 | 10 | 10 | 10 | 10 |

**📊 总计**: **356** 个文件，**48,560** 行代码

</div>

### 🏆 技术栈占比

<div align="center">

| 🎯 **技术栈** | 📈 **占比** | 🔥 **特点** |
|:---:|:---:|:---|
| **🎨 前端 (Vue+TS)** | 45.1% | 现代化响应式界面，TypeScript强类型支持 |
| **🐍 后端 (Python)** | 40.4% | 高性能异步服务，丰富的AI集成 |
| **📚 文档 (MD)** | 7.2% | 完整的项目文档和API说明 |
| **⚙️ 配置 (JSON/YAML)** | 7.3% | 灵活的配置管理和部署支持 |

*💡 项目采用前后端分离架构，代码结构清晰，文档完善*

</div>


---

## 🚀 快速开始

> 🎯 **三种部署方式任你选择** - Docker一键部署 | 本地开发 | 生产环境

<div align="center">

### 📋 系统要求

| 🛠️ **组件** | 🔢 **版本要求** | 📝 **说明** |
|:---:|:---:|:---|
| **Python** | 3.13+ | 后端运行环境 |
| **Node.js** | 18+ | 前端构建环境 |
| **MySQL** | 8.0+ | 主数据库 |
| **Redis** | 7.0+ | 缓存和会话存储 |
| **Docker** | 20.10+ | 容器化部署（推荐） |

</div>


### 🛠️ **方式二：本地开发环境**

<details>
<summary><b>👨‍💻 点击展开本地开发步骤</b></summary>

#### 🔧 **后端环境搭建**

```bash
# 1️⃣ 克隆项目
git clone https://github.com/hhgzeng/toolmind.git
cd toolmind

# 使用pip安装依赖
pip install -r requirements.txt
```


#### ⚙️ **配置文件设置**

创建并编辑配置文件 `src/backend/agentchat/config.yaml`:

#### 🚀 **启动服务**

```bash
# 后端服务
cd src/backend
uvicorn agentchat.main:app --port 7860 --host 0.0.0.0

# 新终端 - 前端服务
cd src/frontend
npm install
npm run dev
```

#### 🌐 **访问地址**

| 🎯 **服务** | 🔗 **地址** | 📝 **说明** |
|:---:|:---:|:---|
| **前端界面** | [localhost:8090](http://localhost:8090) | 用户界面 |
| **后端API** | [localhost:7860](http://localhost:7860) | API服务 |
| **API文档** | [localhost:7860/docs](http://localhost:7860/docs) | Swagger文档 |

</details>


---

## 📦 高级部署指南

> 🎯 **灵活的部署选择** - 从开发测试到生产环境的完整方案

### 🌐 **部署架构选择**

<table>
<tr>
  
<td width="33%">


---

## 📖 文档

### 📚 API文档
- [AgentChat Document](docs/agentchat.md) - agentchat具体文档
- [API Documentation v3.0](docs/api.md) - 最新API文档

### 🔧 开发文档
- **在线API文档**: 启动后端服务后访问 `/docs`
- **前端调试指南**: [src/frontend/DEBUGGING_GUIDE.md](src/frontend/DEBUGGING_GUIDE.md)

### 📋 配置指南

#### 向量数据库配置
- **Milvus**: [安装指南](https://milvus.io/docs/zh/install_standalone-windows.md)
- **ChromaDB**: 项目中已集成，无需额外配置

#### 搜索引擎配置
- **Elasticsearch**: [IK分词器](https://release.infinilabs.com/analysis-ik/stable/)

---

## 🤝 贡献指南

> 💪 **共建AI未来** - 每一个贡献都让AgentChat变得更好

<div align="center">

### 🌟 **我们欢迎所有形式的贡献！**

</div>

<table>
<tr>
<td width="25%">

#### 🐛 **Bug修复**
*发现问题，解决问题*

1. 🔍 搜索已有Issues
2. 📝 创建详细Bug报告
3. 🧪 提供复现步骤
4. 💡 提交修复方案

</td>
<td width="25%">

#### ✨ **功能开发**
*新想法，新功能*

1. 💭 创建Feature Request
2. 📋 详细描述需求场景
3. 🎨 设计实现方案
4. 🚀 开发并测试

</td>
<td width="25%">

#### 📚 **文档完善**
*知识共享，助力他人*

1. 📖 补充API文档
2. ✍️ 编写使用教程
3. 🌍 多语言翻译
4. 🎥 制作视频教程

</td>
<td width="25%">

#### 🧪 **社区支持**
*帮助他人，分享经验*

1. ❓ 回答社区问题
2. 💬 参与技术讨论
3. 🎤 分享使用心得
4. 🤝 推广项目

</td>
</tr>
</table>





## 📄 **许可证**

<div align="center">

本项目采用 **[MIT License](LICENSE)** 开源许可证

*这意味着你可以自由使用、修改和分发本项目 🎉*

</div>

---

<div align="center">
