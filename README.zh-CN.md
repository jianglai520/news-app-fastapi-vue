# 新闻资讯应用 · FastAPI + Vue 3

[English](README.md) · **简体中文**

一个移动端优先的全栈新闻阅读应用：后端是建立在 **MySQL** 之上的异步 **FastAPI** REST API，并用 **Redis** 做读取缓存；前端是 **Vue 3** 单页应用，由 **Vite** 构建，界面基于 **Vant**。

项目定位为学习性质，但结构上是按生产形态搭建的：routers → schemas → crud → models 分层，统一的响应信封，全局异常处理，密码哈希，不透明 Token 认证，以及缓存旁路（cache-aside）读取。

---

## 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [架构](#架构)
- [目录结构](#目录结构)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
  - [1. 数据库](#1-数据库)
  - [2. 后端](#2-后端)
  - [3. 前端](#3-前端)
- [配置](#配置)
- [API 参考](#api-参考)
- [响应格式](#响应格式)
- [认证机制](#认证机制)
- [缓存设计](#缓存设计)
- [数据库表结构](#数据库表结构)
- [前端路由](#前端路由)
- [已知限制](#已知限制)
- [更多文档](#更多文档)

---

## 功能特性

**后端**

- 全链路异步：`SQLAlchemy 2.0` 异步引擎 + `aiomysql`，连接池带 `pool_pre_ping` / `pool_recycle` 保活
- 分层设计 —— `routers/`（HTTP 层）→ `schemas/`（校验与序列化）→ `crud/`（数据访问）→ `models/`（ORM）
- 按分类筛选的分页新闻列表，返回 `total` 与 `hasMore`
- 新闻详情：原子递增浏览量，并推荐相关新闻
- 用户注册 / 登录，密码用 `bcrypt` 哈希
- 不透明 UUID Token 认证（7 天有效期，每个用户一条有效 Token）
- 修改个人资料、修改密码
- 收藏与浏览历史（增 / 列表 / 单删 / 清空）
- 分类与新闻列表走 Redis 缓存旁路，Redis 故障时自动降级查库
- 所有响应用统一的 `{ code, message, data }` 信封
- 全局异常处理器覆盖 `HTTPException`、`IntegrityError`、`SQLAlchemyError` 与未捕获异常

**前端**

- Vue 3 `<script setup>` 单页应用，路由懒加载
- Pinia 管理用户、新闻、收藏、历史、主题、语言六类状态，并持久化到 `localStorage`
- Vant 4 移动端组件库
- 通过 `vue-i18n` 支持中英文切换
- 明暗主题切换
- AI 问答页面接入 DashScope 兼容接口（见[已知限制](#已知限制)）
- 开发服务器代理，浏览器只与同源通信

---

## 技术栈

| 层次 | 技术 | 版本 |
|---|---|---|
| 语言 | Python | 3.14 |
| Web 框架 | FastAPI | 0.125.0 |
| ASGI 服务器 | Uvicorn | 0.38.0 |
| ORM | SQLAlchemy（异步） | 2.0.45 |
| 数据库驱动 | aiomysql / PyMySQL | 0.3.2 / 1.1.2 |
| 数据库 | MySQL | 8.0 |
| 缓存 | Redis（redis-py 异步客户端） | ≥ 5.0 |
| 数据校验 | Pydantic | 2.12.5 |
| 密码哈希 | passlib + bcrypt | 1.7.4 / 3.2.2 |
| 前端框架 | Vue | 3.5 |
| 构建工具 | Vite | 7.1 |
| 状态管理 | Pinia（含持久化插件） | 3.0 / 4.5 |
| 路由 | Vue Router | 4.5 |
| UI 组件库 | Vant | 4.9 |
| 国际化 | vue-i18n | 9.8 |
| HTTP 客户端 | axios | 1.12 |

---

## 架构

```
┌──────────────────────────┐        ┌───────────────────────────┐
│  Vue 3 SPA (Vite :5173)  │        │   FastAPI (Uvicorn :8000) │
│                          │  /api  │                           │
│  视图 ← Pinia 状态       │ ─────► │  routers → schemas        │
│       ← axios            │  代理  │         → crud → models   │
└──────────────────────────┘        └─────────┬─────────┬───────┘
                                              │         │
                                     异步 SQL │         │ 缓存旁路
                                              ▼         ▼
                                    ┌──────────────┐ ┌─────────┐
                                    │ MySQL 8      │ │ Redis   │
                                    │ news_app     │ │ db 0    │
                                    └──────────────┘ └─────────┘
```

以带缓存的接口（如 `GET /api/news/categories`）为例，一次请求的流程是：

1. 路由通过 `get_db` 依赖注入一个 `AsyncSession`；
2. `crud/news_cache.py` 先向 Redis 请求 `news:categories`；
3. 命中缓存则完全跳过 ORM；未命中才查库，并把 JSON 结果按 TTL 写回；
4. 路由把数据套进统一信封返回。

---

## 目录结构

```
news-app-fastapi-vue/
├── .gitignore
├── README.md                    # 英文版
├── README.zh-CN.md              # 本文件
│
├── news_app_backend/
│   ├── main.py                  # 应用入口、lifespan、CORS、路由注册
│   ├── requirements.txt
│   ├── database.sql             # 建表 + 种子数据（8 张表，403 条演示新闻）
│   ├── .env                     # 本地密钥，不进版本库
│   ├── config/
│   │   ├── db_config.py         # 异步引擎、会话工厂、get_db / close_db
│   │   └── cache_config.py      # Redis 客户端与读写封装
│   ├── models/                  # SQLAlchemy ORM 模型
│   │   ├── news.py              # Category、News
│   │   ├── users.py             # User、UserToken
│   │   ├── favorite.py          # Favorite
│   │   └── history.py           # History
│   ├── schemas/                 # Pydantic 请求 / 响应模型
│   ├── crud/                    # 数据访问函数
│   │   ├── news.py              # 详情、浏览量递增、相关新闻
│   │   ├── news_cache.py        # 带 Redis 缓存的分类 / 列表查询
│   │   ├── users.py             # 用户与 Token 操作
│   │   ├── favorite.py
│   │   └── history.py
│   ├── routers/                 # HTTP 层，每个资源一个路由文件
│   ├── cache/
│   │   └── news_cache.py        # 新闻缓存的 key 与 TTL
│   ├── utils/
│   │   ├── auth.py              # get_current_user 依赖
│   │   ├── security.py          # bcrypt 加密 / 校验
│   │   ├── response.py          # 成功响应信封
│   │   ├── exception.py         # 异常处理器实现
│   │   └── exception_handlers.py
│   └── docs/                    # 中文设计文档
│       ├── API接口规范文档.md
│       └── 项目后端设计说明文档.md
│
└── news_app_frontend/
    ├── package.json
    ├── vite.config.js           # 开发服务器 + /api → :8000 代理
    ├── index.html
    └── src/
        ├── main.js              # 应用启动、Vant 注册、主题初始化
        ├── App.vue
        ├── config/api.js        # API 基址与 AI 问答配置
        ├── router/index.js      # 12 条路由，懒加载
        ├── store/               # Pinia 状态（user、theme、language、modules/）
        ├── views/               # 页面组件
        ├── components/          # NewsItem、TabBar 等
        ├── i18n/                # 中英文语言包
        └── style.css
```

---

## 环境要求

| 依赖 | 说明 |
|---|---|
| Python **3.14+** | 项目按 3.14 开发并锁定依赖 |
| Node.js **20+** | Vite 7 要求 Node 20.19+ 或 22.12+ |
| MySQL **8.0** | 监听 `127.0.0.1:3306` |
| Redis **5+** | 监听 `127.0.0.1:6379`；严格说不装也能跑（失败会降级查库），但建议装上 |

> **重要**：后端必须**在 `news_app_backend/` 目录内启动**。所有内部导入（`from config…`、`from crud…`、`from models…`）都以该目录为根解析，从仓库根目录启动会报 `ModuleNotFoundError`。

---

## 快速开始

### 1. 数据库

SQL 脚本是自包含的：会创建 `news_app` 库、8 张表，并写入 8 个分类和 403 条演示新闻。

```powershell
cd news_app_backend

# Windows PowerShell 下必须用 cmd /c 包一层，因为 PowerShell 把 < 当特殊符号；
# --default-character-set=utf8mb4 也不能省，否则中文会乱码
cmd /c "mysql --default-character-set=utf8mb4 -u root -p < database.sql"
```

需要完全重来一遍时（脚本里建表用的是 `CREATE TABLE IF NOT EXISTS`，直接重复导入会在分类唯一索引上报 1062 冲突）：

```powershell
cmd /c 'mysql -u root -p -e "DROP DATABASE IF EXISTS news_app;"'
cmd /c "mysql --default-character-set=utf8mb4 -u root -p < database.sql"
```

验证（在 CP936 控制台里用 `gbk` 读取，中文才显示正常）：

```powershell
cmd /c 'mysql --default-character-set=gbk -u root -p -e "SHOW TABLES; SELECT COUNT(*) FROM news;" news_app'
```

### 2. 后端

```powershell
cd news_app_backend

# 创建虚拟环境并安装依赖
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 按下方「配置」一节创建 .env，然后启动
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

服务监听 `http://127.0.0.1:8000`。

- 交互式接口文档：<http://127.0.0.1:8000/docs>
- 存活探针：`GET /` 返回 `{"msg": "this is a news_app_fastapi_vue"}`

启动时 `lifespan` 会先对 MySQL 执行一次 `SELECT 1`，所以 `DATABASE_URL` 配错会**在启动阶段就失败**，而不是等第一个请求才报错；关闭时释放连接池。

### 3. 前端

```powershell
cd news_app_frontend
npm install
npm run dev
```

开发服务器在 `http://localhost:5173`。`vite.config.js` 把 `/api/*` 代理到 `http://127.0.0.1:8000`，所以浏览器发出的是同源请求，开发阶段不涉及跨域协商。

生产构建：

```powershell
npm run build      # 输出到 dist/
npm run preview    # 本地预览构建结果
```

如果前端与后端部署在不同源，构建时设置 `VITE_API_BASE_URL`（例如 `https://api.example.com`）；`src/config/api.js` 会读取它，留空则保持走代理。

---

## 配置

后端配置放在 `news_app_backend/.env`（已被 Git 忽略）：

```ini
# mysql+aiomysql://<用户>:<密码>@<主机>:<端口>/<库名>?charset=utf8mb4
DATABASE_URL=mysql+aiomysql://root:你的密码@127.0.0.1:3306/news_app?charset=utf8mb4

# 是否打印每条 SQL（仅开发时开启）
DB_ECHO=false
```

| 变量 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `DATABASE_URL` | 是 | — | SQLAlchemy 异步连接串，缺失会在导入时抛 `RuntimeError` |
| `DB_ECHO` | 否 | `false` | 设为 `true` 会打印所有执行的 SQL |

Redis 连接参数目前硬编码在 `config/cache_config.py`：

| 配置项 | 值 |
|---|---|
| 主机 | `localhost` |
| 端口 | `6379` |
| 数据库编号 | `0` |
| 协议 | RESP2（强制指定，用于规避客户端与服务器版本不兼容） |

---

## API 参考

所有接口都以 `/api` 为前缀。“需要认证”表示请求必须在 `Authorization` 头里携带有效 Token。

### 新闻

| 方法 | 路径 | 认证 | 参数 | 说明 |
|---|---|---|---|---|
| GET | `/api/news/categories` | — | `skip`（0）、`limit`（100） | 分类列表，缓存 2 小时 |
| GET | `/api/news/list` | — | `categoryId` **必填**、`page`（1）、`pageSize`（10，≤100） | 按分类分页取新闻，缓存 30 分钟 |
| GET | `/api/news/detail` | — | `id` **必填** | 正文；浏览量 +1；同时返回最多 5 条相关新闻 |

`GET /api/news/list` 的 `data` 结构：

```json
{
  "list": [ { "id": 1, "title": "…", "description": "…", "image": "…", "author": "…",
              "categoryId": 1, "views": 12500, "publishedTime": "2024-01-01T08:00:00" } ],
  "total": 50,
  "hasMore": true
}
```

### 用户

| 方法 | 路径 | 认证 | 请求体 / 参数 | 说明 |
|---|---|---|---|---|
| POST | `/api/user/register` | — | `{ username, password }` | 注册，返回 Token 与用户信息 |
| POST | `/api/user/login` | — | `{ username, password }` | 登录，返回 Token 与用户信息 |
| GET | `/api/user/info` | ✅ | — | 当前用户信息 |
| PUT | `/api/user/update` | ✅ | `{ nickname, avatar, gender, bio, phone }` | 更新个人资料 |
| PUT | `/api/user/password` | ✅ | `{ oldPassword, newPassword }` | 修改密码（新密码 ≥ 6 位） |

### 收藏

| 方法 | 路径 | 认证 | 请求体 / 参数 | 说明 |
|---|---|---|---|---|
| GET | `/api/favorite/check` | ✅ | `newsId` **必填** | 返回 `{ isFavorite: bool }` |
| POST | `/api/favorite/add` | ✅ | `{ newsId }` | 添加收藏 |
| DELETE | `/api/favorite/remove` | ✅ | `newsId` **必填** | 取消单条收藏 |
| GET | `/api/favorite/list` | ✅ | `page`、`pageSize` | 分页收藏列表，含 `favoriteId` / `favoriteTime` |
| DELETE | `/api/favorite/clear` | ✅ | — | 清空当前用户全部收藏 |

### 浏览历史

| 方法 | 路径 | 认证 | 请求体 / 参数 | 说明 |
|---|---|---|---|---|
| POST | `/api/history/add` | ✅ | `{ newsId }` | 记录一次浏览 |
| GET | `/api/history/list` | ✅ | `page`（1）、`pageSize`（10） | 分页历史，含 `historyId` / `viewTime` |
| DELETE | `/api/history/delete/{history_id}` | ✅ | 路径参数 | 删除单条历史 |
| DELETE | `/api/history/clear` | ✅ | — | 清空当前用户历史 |

### 其他

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 存活探针 |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc |

---

## 响应格式

所有接口都返回同一种信封：

```json
{ "code": 200, "message": "获取新闻列表成功", "data": { } }
```

由全局异常处理器产生的错误保持同样结构，`code` 与 HTTP 状态码一致：

```json
{
  "code": 401,
  "message": "无效的令牌或已经过期的令牌",
  "data": null
}
```

异常处理器与状态码对应关系：

| 处理器 | 状态码 | 典型 message |
|---|---|---|
| `HTTPException` | 按抛出时指定 | 抛出的 `detail` |
| `IntegrityError` | 400 | `用户名已存在`、`关联数据不存在`、`数据约束冲突` |
| `SQLAlchemyError` | 500 | `数据库操作失败，请稍后重试` |
| `Exception` | 500 | `服务器内部错误` |

当 `utils/exception.py` 里的 `DEBUG_MODE = True` 时，4xx / 5xx 的 `data` 字段还会带上 `error_type`、`error_detail`、`traceback`、`path`。上线前务必关掉。

---

## 认证机制

接口使用**不透明 Bearer Token**，不是 JWT。

1. `POST /api/user/register` 或 `POST /api/user/login` 会生成一个 UUID v4 Token，写入 `user_token` 表，有效期 **7 天**，并返回给客户端；
2. 每个用户只有**一条**有效 Token：再次登录会覆盖旧 Token，从而让旧会话失效；
3. 客户端把 Token 放在 `Authorization` 头里。因为 `utils/auth.py` 会剥掉可选的 `Bearer ` 前缀，下面两种写法都有效：

   ```
   Authorization: 550e8400-e29b-41d4-a716-446655440000
   Authorization: Bearer 550e8400-e29b-41d4-a716-446655440000
   ```

4. `get_current_user` 按 Token 查库，查不到或已过期就返回 `401`，否则把 `User` ORM 对象交给路由函数。

密码用 `passlib` 的 bcrypt 方案哈希，明文既不落库也不进日志。

没有登出接口，也没有 Token 刷新机制 —— 前端登出（`store.logout()`）只是清空本地状态，服务端 Token 靠自然过期失效。

---

## 缓存设计

采用缓存旁路（cache-aside），实现在 `cache/news_cache.py`，由 `crud/news_cache.py` 调用。

| Key 模式 | 内容 | TTL |
|---|---|---|
| `news:categories` | 序列化后的分类列表 | 7200 秒（2 小时） |
| `news_list{category}:{page}:{pageSize}` | 某一页新闻数据 | 1800 秒（30 分钟） |

设计要点：

- 不同类型数据设置不同 TTL，避免所有 Key 同时过期引发缓存雪崩；
- 值以 JSON 字符串存储（`ensure_ascii=False`，中文不会被转义）；
- 所有 Redis 调用都包了 `try/except`，失败时返回 `None`，因此 Redis 挂掉只会退化成直接查库，不会让接口 500；
- 目前**没有写操作失效逻辑**，直接改 MySQL 的数据要等 TTL 到期才会生效。

---

## 数据库表结构

数据库 `news_app`，字符集 `utf8mb4`，引擎 InnoDB。

| 表 | 用途 | 关键字段 |
|---|---|---|
| `user` | 用户账号 | `username`（唯一）、`password`（bcrypt）、`nickname`、`avatar`、`gender`（枚举）、`bio`、`phone`（唯一） |
| `user_token` | 有效登录令牌 | `user_id` 外键、`token`（唯一）、`expires_at` |
| `news_category` | 新闻分类 | `name`（唯一）、`sort_order` |
| `news` | 新闻文章 | `title`、`description`、`content`、`image`、`author`、`category_id` 外键、`views`、`publish_time` |
| `related_news` | 预留的新闻关联表 | `news_id`、`related_news_id` |
| `favorite` | 收藏 | `user_id` + `news_id` 联合唯一 |
| `history` | 浏览历史 | `user_id` 外键、`news_id` 外键、`view_time` |
| `ai_chat` | 预留的 AI 对话记录 | `user_id` 外键、`message`、`response` |

`user`、`news_category`、`news` 三张表都带 `created_at` / `updated_at`，由数据库维护。

---

## 前端路由

| 路径 | 视图 | 说明 |
|---|---|---|
| `/` | — | 重定向到 `/home` |
| `/home` | `Home.vue` | 分类标签的新闻流，支持下拉刷新与无限加载（keep-alive） |
| `/news/detail/:id` | `NewsDetail.vue` | 正文、收藏切换、相关新闻 |
| `/category` | `Category.vue` | 分类浏览（keep-alive） |
| `/favorite` | `Favorite.vue` | 收藏列表，分页 |
| `/history` | `History.vue` | 浏览历史，可单删 / 清空 |
| `/aichat` | `AIChat.vue` | AI 问答界面（见限制说明） |
| `/my` | `My.vue` | 个人中心（keep-alive） |
| `/profile` | `Profile.vue` | 编辑个人资料 |
| `/settings` | `Settings.vue` | 主题与语言设置 |
| `/login`、`/register` | `Login.vue`、`Register.vue` | 登录与注册 |

状态管理：`store/user.js`（Token + 用户信息）、`store/modules/news.js`、`store/modules/favorite.js`、`store/modules/history.js`、`store/theme.js`、`store/language.js`，全部通过 `pinia-plugin-persistedstate` 持久化到 `localStorage`。

---

## 已知限制

以下都是已知的取舍或待办，不影响当前开发，但上线前必须处理。

- **CORS 完全放开**：`main.py` 里 `allow_origins=["*"]` 同时又开了 `allow_credentials=True`。浏览器对这种组合的带凭据请求会直接拒绝，生产环境也不安全，应改成明确列出源。
- **调试 traceback 暴露在外**：`utils/exception.py` 的 `DEBUG_MODE = True` 会把堆栈写进错误响应的 `data` 字段。
- **AI 的 Key 会随前端发布出去**：`AIChat.vue` 用 `fetch` 直接请求 DashScope 兼容接口，Key 来自 `src/config/api.js`，会被打进公开的 JS 产物。正式使用应改由后端转发。
- **缓存没有失效机制**：直接改库的数据要等 TTL 到期才反映到接口。
- **`GET /api/favorite/list` 的 `page` 默认值是 10**（`Query(10, ge=1)`），不是 1。
- **时间戳语义不统一**：`Favorite.created_at` 用 `datetime.utcnow`，其他模型用本地 `datetime.now`，收藏时间与其余表存在时区差。
- **存在多个 declarative Base**：`models/news.py`、`models/users.py`、`models/favorite.py`、`models/history.py` 各自声明了 `Base`，因此无法使用跨模型的 `relationship()`，join 都在 `crud/` 里手写。
- **路由没有守卫**：`router.beforeEach` 只设置了页面标题，受保护页面依赖接口返回 `401` 来兜底。
- **Redis 参数无法用环境变量配置**（硬编码在 `config/cache_config.py`），项目也没有 docker-compose，默认本机已安装 MySQL 与 Redis。

---

## 更多文档

中文设计文档位于 `news_app_backend/docs/`：

- `API接口规范文档.md` —— 接口契约与约定
- `项目后端设计说明文档.md` —— 后端设计思路

需要始终与代码同步的接口文档，请启动后端后访问 `/docs`（Swagger UI），它由接口实际使用的 schema 生成。

---

## 项目定位

这是一个学习项目，覆盖异步 FastAPI 的常见写法、后端分层设计、Redis 缓存旁路，以及 Vue 3 移动端前端。`.env` 里的凭据仅为本地开发使用 —— 在其他任何地方使用这份代码前请先更换。
