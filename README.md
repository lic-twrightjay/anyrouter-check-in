<div align="center">

# 🚀 AnyRouter Check-In

**Multi-platform, multi-account auto check-in for NewAPI / OneAPI sites**

[![GitHub Actions](https://github.com/shenhao-stu/anyrouter-check-in/workflows/AnyRouter%20%E8%87%AA%E5%8A%A8%E7%AD%BE%E5%88%B0/badge.svg)](https://github.com/shenhao-stu/anyrouter-check-in/actions)
[![Python](https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Playwright](https://img.shields.io/badge/playwright-enabled-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000?logo=ruff&logoColor=white)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/github/license/shenhao-stu/anyrouter-check-in?color=blue)](LICENSE)
[![Stars](https://img.shields.io/github/stars/shenhao-stu/anyrouter-check-in?style=social)](https://github.com/shenhao-stu/anyrouter-check-in/stargazers)

[简体中文](#-功能特性) · [English](#-features)

**⭐ 维护开源不易，如果本项目帮助到了你，请帮忙点个 Star，谢谢！**

</div>

---

## ✨ 功能特性

- 🌐 **多平台支持** — 兼容所有 NewAPI / OneAPI 站点
- 👥 **多账号签到** — 同一平台多账号同时签到
- 🔌 **插件一键添加** — Chrome 扩展 / 油猴脚本自动注册新平台，无需手动改 Secrets
- 🔄 **自动重试** — 5xx / 网络超时自动重试，抗抖动
- 🛡️ **WAF 绕过** — Playwright 自动获取 WAF cookies
- 📣 **多渠道通知** — 飞书 / 钉钉 / 企微 / Telegram / Email / Bark / Gotify / PushPlus / Server 酱
- ⏰ **定时执行** — GitHub Actions 每 6 小时自动运行

> 内置支持 [AnyRouter](https://anyrouter.top/register?aff=gSsN) 和 [AgentRouter](https://agentrouter.org)，其它平台通过插件或 `PROVIDERS` secret 一键接入。

推荐搭配 [Auo](https://github.com/millylee/auo) — 支持任意 Claude Code Token 切换的工具。

---

## 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────┐
│                  GitHub Actions                      │
│  ┌───────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Secrets   │→ │ checkin  │→ │ Notifications    │  │
│  │ injection │  │ .py      │  │ (飞书/钉钉/TG…)  │  │
│  └───────────┘  └──────────┘  └──────────────────┘  │
└────────────────────────▲────────────────────────────┘
                         │ push secrets
          ┌──────────────┴──────────────┐
          │  Chrome Extension /         │
          │  Tampermonkey Userscript    │
          │  (auto-sync cookies &       │
          │   register new platforms)   │
          └─────────────────────────────┘
```

---

## 🚀 快速开始

### 1️⃣ Fork 本仓库

点击右上角 **Fork** 按钮。

### 2️⃣ 安装插件并配置 GitHub PAT

推荐使用 **Chrome 扩展**或**油猴脚本**（见 [下方详细说明](#-chrome-扩展anyrouter-cookie-updater)）自动同步 cookie。

插件需要一个 GitHub Personal Access Token（PAT）：

1. 访问 [GitHub Settings → Fine-grained tokens](https://github.com/settings/personal-access-tokens)
2. 新建 token，**Resource owner** 选仓库所属用户，**Repository access** 选择你 fork 的仓库
3. 若插件 Environment 填写了 `production`：在 **Repository permissions → Environments** 开启 **Read and write**；若 Environment 留空（Repository Secrets）：开启 **Secrets → Read and write**
4. 如果使用 [Classic PAT](https://github.com/settings/tokens)，需勾选 `repo` scope。两类 PAT 任选其一，无法由插件自动扩大权限
5. 将 token 填入插件设置面板

### 3️⃣ 在插件中添加账号

```json
[
  { "domain": "https://anyrouter.top" },
  { "domain": "https://agentrouter.org" },
  { "domain": "https://api.freestyle.cc.cd" },
  { "domain": "https://computetoken.ai" }
]
```

每行只需填写 `domain`，插件会自动：
- 🍪 提取浏览器 `session` cookie
- 🔍 调用 `/api/user/self` 解析 `api_user`
- 🔑 生成 `ANYROUTER_ACCOUNT_{api_user}_{PROVIDER}` secret 并推送
- 📦 更新 `PROVIDERS` secret，自动注册新平台

### 4️⃣ 设置 Environment Secret（仅首次）

1. 仓库 **Settings → Environments → New environment** → 新建 `production`
2. 添加 secret `ANYROUTER_ACCOUNTS`（账号 JSON 数组）

> 💡 如果所有账号都通过 `ANYROUTER_ACCOUNT_*` 独立管理（推荐），`ANYROUTER_ACCOUNTS` 可设为 `[]`。

> ⚠️ **`[]` 表示不在基础列表中存储账号，不会自动创建任何账号。**
> 请先在插件的 GitHub 配置中确认 **Owner 为 `lic-twrightjay`（如使用该 Fork）**、
> **仓库名为 `anyrouter-check-in`、Environment 为 `production`**，
> 点击 **保存 → 同步**，并确认同步结果显示 **全部账号成功**，目标仓库及 Environment 正确。
> 插件中的 **「测试」只检查 Cookie / api_user，不会上传到 GitHub Secrets**。
> 然后到仓库 **Settings → Environments → production → Environment secrets** 确认已经出现
> `ANYROUTER_ACCOUNT_{api_user}_{PROVIDER}` 等独立 Secret（仅检查名称，勿公开值）。
> 若插件使用 **Repository Secrets**，独立账号 Secret 也可以被当前绑定 `production` 的签到工作流读取（同名 Environment Secret 优先）；无需改动工作流。
> 如果插件同步到另一个仓库/Environment，需先修正同步目标并重新运行。
> 工作流开始时会先预检可见账号数量；若为 0，会在安装浏览器前明确报错。

### 🧯 同步返回 0/1、403 或 404 时

插件中的绿色「测试成功」只说明浏览器能提取 Cookie / `api_user`，**并不代表已上传 GitHub**。请点击「立即同步」，检查错误文本（错误提示会保持显示），必要时打开插件「日志」：

| API 返回 | 原因与解决方式 |
| :--- | :--- |
| 401 | PAT 无效、已撤销或过期，重新生成 PAT 并在插件保存 |
| 403 | **Fine-grained PAT** 选择正确 Resource owner 和仓库，Environment 目标授予 **Environments: Read and write**；Repository Secrets 目标授予 **Secrets: Read and write**；**Classic PAT** 选择 **repo** scope |
| 404 | 检查 Owner / Repo / Environment 是否准确（此仓库为 `lic-twrightjay/anyrouter-check-in`，Environment 名为 `production`）；GitHub 也可能用 404 表示权限不足 |
| 422 | 检查 `env_key_suffix`：只使用英文字母、数字和下划线 |
| 网络或限流 | 检查 GitHub API 网络、代理或稍后重试 |

新版本插件使用 GitHub 官方 REST 路径 `/repos/{owner}/{repo}/environments/{environment_name}/secrets`；只要 PAT 权限足够，即可加密写入。插件**不能自动修复 PAT 授权**，也不会在 Environment 写入失败时擅自改写到 Repository Secrets。

### 🧰 不依赖插件的手动恢复（两个任选其一）

**方案 A：添加独立账号 Secret，保留 `ANYROUTER_ACCOUNTS=[]`**

1. 从已登录站点的浏览器开发者工具 → **Application → Cookies** 中复制自己的 `session` 值；`api_user` 可在插件账号的测试结果中看到。Cookie 是登录凭据，只能在自己设备上复制，切勿发布到 Issue / 截图 / 聊天。
2. 前往 [Environments](https://github.com/lic-twrightjay/anyrouter-check-in/settings/environments) → `production` → **Environment secrets → Add secret**；或前往 [Repository Secrets](https://github.com/lic-twrightjay/anyrouter-check-in/settings/secrets/actions) → **New repository secret**。两处均可被此工作流读取。
3. Secret 名称按 `ANYROUTER_ACCOUNT_{api_user}_{PROVIDER}` 设置。例如 AgentRouter 用户 ID 为 `356997` 时：`ANYROUTER_ACCOUNT_356997_AGENTROUTER`。
4. Secret Value 填入以下 JSON，**把示例占位符替换成你自己的 Cookie**，随后保存：

   ```json
   {
     "cookies": { "session": "请替换为自己浏览器中的session值" },
     "api_user": "356997",
     "provider": "agentrouter",
     "domain": "https://agentrouter.org"
   }
   ```

   AnyRouter 账号则将 provider 改为 `anyrouter`、domain 改为 `https://anyrouter.top`，并替换对应 ID 与 Cookie。不同账号各建一个独立 Secret；**不要把 Secret Value 放进仓库文件**。
5. 确保 `production` 中的 `ANYROUTER_ACCOUNTS` 仍为 `[]`。点击 [Actions → AnyRouter 自动签到](https://github.com/lic-twrightjay/anyrouter-check-in/actions/workflows/checkin.yml) → **Run workflow**，选择 `main`。检查「验证并注入账号 Secrets」输出 `0 base, 1 individual`（或实际账号数）后继续运行。

**方案 B：直接使用 `ANYROUTER_ACCOUNTS` 基础 JSON**

无需建立任何 `ANYROUTER_ACCOUNT_*`。进入 `production` → 编辑 `ANYROUTER_ACCOUNTS`，将值由 `[]` 改成 **JSON 数组**，例如：

```json
[
  {
    "cookies": { "session": "请替换为自己的session值" },
    "api_user": "356997",
    "provider": "agentrouter",
    "domain": "https://agentrouter.org"
  }
]
```

重新运行工作流，预检应输出 `1 base, 0 individual`。此方案只需要一个 Environment Secret，适合暂时无法通过插件更新独立 Secrets 的情况。

### 5️⃣ 启用 GitHub Actions

在 **Actions** 选项卡启用 "AnyRouter 自动签到" workflow，点击 **Run workflow** 手动触发一次验证。

---

## 📋 多账号配置格式

### ANYROUTER_ACCOUNTS（基础账号列表）

```json
[
  {
    "name": "AnyRouter 主账号",
    "cookies": { "session": "account1_session_value" },
    "api_user": "123456"
  },
  {
    "name": "AgentRouter 备用",
    "provider": "agentrouter",
    "cookies": { "session": "account2_session_value" },
    "api_user": "789012"
  }
]
```

| 字段 | 必填 | 说明 |
| :--- | :---: | :--- |
| `cookies` | ✅ | 身份验证 cookies |
| `api_user` | ✅ | 请求头 `new-api-user` 的值 |
| `provider` | ❌ | 服务商标识，默认 `anyrouter` |
| `name` | ❌ | 显示名称，用于日志和通知 |

> 📌 `anyrouter` 和 `agentrouter` 已内置；其它平台通过 `PROVIDERS` secret 或插件自动注册。

### 🔑 获取 cookies 和 api_user

通过 F12 开发者工具：

- **session** → Application → Cookies → 复制 `session` 值（重新登录后获取，有效期约 1 个月）
- **api_user** → Network → 过滤 Fetch/XHR → 找到含 `New-Api-User` 请求头的请求

<details>
<summary>📸 截图参考</summary>

![获取 cookies](./assets/request-session.png)
![获取 api_user](./assets/request-api-user.png)

</details>

---

## 🗂️ 单账号独立管理（ANYROUTER_ACCOUNT_*）

推荐方式。每个账号单独一个 secret，插件自动维护。

### 命名规范

```
ANYROUTER_ACCOUNT_{api_user}_{PROVIDER}
```

示例：
```
ANYROUTER_ACCOUNT_123456_ANYROUTER
ANYROUTER_ACCOUNT_789012_AGENTROUTER
ANYROUTER_ACCOUNT_7535_FREESTYLE
ANYROUTER_ACCOUNT_760_COMPUTETOKEN
```

> ⚠️ `api_user` 是各平台内部自增 ID，不同平台间可能重复，必须加平台标识才能唯一区分。

### Secret 内容格式

```json
{
  "cookies": { "session": "session_value" },
  "api_user": "760",
  "provider": "computetoken",
  "domain": "https://computetoken.ai"
}
```

### 合并规则

- 🔄 独立 secret 与 `ANYROUTER_ACCOUNTS` 中 `api_user` 匹配时，字段会**覆盖**主配置
- ➕ 无匹配时作为新账号追加
- 🔑 去重键为 `(api_user, provider)` 组合

---

## 🌍 新平台接入（全自动）

只需在插件账号列表中添加新域名，点击"同步所有账号"，插件自动完成：

1. 🍪 提取该站点的 session cookie
2. 🔑 推送 `ANYROUTER_ACCOUNT_*` secret（含 `provider` 和 `domain`）
3. 📦 更新 `PROVIDERS` secret

**全程无需手动修改任何 GitHub Secret。**

### 🏷️ 平台 Tag 命名规则

| 域名 | 自动生成 Tag |
| :--- | :--- |
| `https://anyrouter.top` | `ANYROUTER` |
| `https://api.freestyle.cc.cd` | `FREESTYLE` |
| `https://computetoken.ai` | `COMPUTETOKEN` |
| `https://my-custom-api.example.com` | `MY` |

> 前缀 `www`、`api`、`app`、`new`、`newapi`、`welfare` 会被自动跳过。

---

## ⚙️ 手动配置 Provider（可选）

若不使用插件，可手动配置 `PROVIDERS` secret：

<details>
<summary>📝 基础配置（仅域名）</summary>

```json
{
  "computetoken": { "domain": "https://computetoken.ai" },
  "freestyle": { "domain": "https://api.freestyle.cc.cd" }
}
```

</details>

<details>
<summary>📝 完整配置（自定义路径 + WAF）</summary>

```json
{
  "customrouter": {
    "domain": "https://custom.example.com",
    "login_path": "/auth/login",
    "sign_in_path": "/api/checkin",
    "user_info_path": "/api/profile",
    "api_user_key": "New-Api-User",
    "bypass_method": "waf_cookies",
    "waf_cookie_names": ["acw_tc", "cdn_sec_tc", "acw_sc__v2"]
  }
}
```

</details>

| 字段 | 必填 | 默认值 | 说明 |
| :--- | :---: | :--- | :--- |
| `domain` | ✅ | — | 服务商域名 |
| `login_path` | ❌ | `/login` | 登录页路径（WAF 模式） |
| `sign_in_path` | ❌ | `/api/user/sign_in` | 签到 API（404 自动回退 `/api/user/checkin`） |
| `user_info_path` | ❌ | `/api/user/self` | 用户信息 API |
| `api_user_key` | ❌ | `new-api-user` | 请求头用户 ID 键名 |
| `bypass_method` | ❌ | `null` | `"waf_cookies"` 或 `null` |
| `waf_cookie_names` | ❌ | — | WAF cookie 名称列表 |

### 🛡️ 内置平台

| 平台 | WAF | 签到方式 |
| :--- | :---: | :--- |
| `anyrouter` | ✅ waf_cookies | `/api/user/sign_in` |
| `agentrouter` | ✅ waf_cookies | 查询用户信息时自动签到 |
| ~~`heibai`~~ | ~~cap.js PoW~~ | ~~已停用（账号因自动签到检测被封禁）~~ |

> 其余平台通过 `PROVIDERS` secret 或插件自动同步。标准 new-api / one-api 站点使用默认路径，404 时自动回退到 `/api/user/checkin`。

---

## 🧩 Chrome 扩展：AnyRouter Cookie Updater

位于仓库 `AnyRouter Cookie Updater/` 目录。

### 工作原理

1. 🍪 从浏览器 cookie jar 提取 `session` cookie
2. 🔍 调用 `/api/user/self` 解析 `api_user`（优先读 localStorage，零网络请求）
3. 🔐 使用 libsodium sealed box 加密后推送 `ANYROUTER_ACCOUNT_*` secret
4. 📦 同步结束后更新 `PROVIDERS` secret，自动注册非内置平台

### 📥 安装

1. 打开 `chrome://extensions/`
2. 开启右上角"开发者模式"
3. 点击"加载已解压的扩展程序" → 选择 `AnyRouter Cookie Updater/` 目录

### 🔧 配置

| 配置项 | 说明 |
| :--- | :--- |
| 🔑 GitHub PAT | Fine-grained：Environment 目标需 `Environments` Read & Write，Repository Secrets 目标需 `Secrets` Read & Write；Classic：`repo` scope |
| 👤 仓库 Owner | 你的 GitHub 用户名 |
| 📦 仓库名称 | 如 `anyrouter-check-in` |
| 🏷️ Environment | 如 `production`（留空则推送到 Repository Secrets，现有签到工作流也能读取） |
| 📋 账号列表 | 每行一个站点，只需填 `domain` |
| ⏰ 同步间隔 | 建议 360 分钟（6 小时），0 = 仅手动 |

---

## 🐒 Tampermonkey 脚本

油猴脚本 `anyrouter-cookie-updater.user.js`，支持 Chrome / Firefox / Edge / Safari。

### 📥 安装

- **方式一（推荐）**：安装 [Tampermonkey](https://www.tampermonkey.net/) 后，直接打开仓库中的 `anyrouter-cookie-updater.user.js`
- **方式二**：Tampermonkey 管理面板 → "添加新脚本" → 粘贴内容保存

### 📋 菜单命令

| 命令 | 说明 |
| :--- | :--- |
| ⚙️ 设置 / 账号配置 | 打开配置面板 |
| 🔄 立即同步本站 | 提取当前站点 cookie 并推送 |
| 🔄 同步所有账号 | 遍历所有账号逐个同步，并更新 `PROVIDERS` |
| 📋 查看日志 | 查看最近 80 条操作日志 |

### 🔄 Chrome 扩展 vs 油猴脚本

| 特性 | Chrome 扩展 | 油猴脚本 |
| :--- | :---: | :---: |
| 支持浏览器 | Chrome / Edge | 全平台 |
| 需要开发者模式 | ✅ | ❌ |
| 后台定时触发 | ✅ | ⚠️ 页面加载时 |
| 跨站点 cookie | ✅ | ⚠️ 需在对应站点 |
| 单账号测试 | ✅ | ✅ |

---

## 📣 通知配置

在仓库 **Settings → Environments → production → Environment secrets** 中添加：

<details>
<summary>📧 邮箱（SMTP）</summary>

| 变量 | 说明 |
| :--- | :--- |
| `EMAIL_USER` | 发件人地址 / SMTP 登录名 |
| `EMAIL_PASS` | 密码 / 授权码 |
| `EMAIL_SENDER` | 发件人显示地址（可选） |
| `CUSTOM_SMTP_SERVER` | 自定义 SMTP 服务器（可选） |
| `EMAIL_TO` | 收件人地址 |

</details>

<details>
<summary>🤖 钉钉机器人</summary>

`DINGDING_WEBHOOK` — Webhook 地址（自定义关键词填 `AnyRouter`）

</details>

<details>
<summary>🐦 飞书机器人</summary>

`FEISHU_WEBHOOK` — Webhook 地址

</details>

<details>
<summary>💬 企业微信机器人</summary>

`WEIXIN_WEBHOOK` — Webhook 地址

</details>

<details>
<summary>📱 PushPlus / Server 酱</summary>

- `PUSHPLUS_TOKEN` — PushPlus Token
- `SERVERPUSHKEY` — Server 酱 SendKey

</details>

<details>
<summary>✈️ Telegram Bot</summary>

- `TELEGRAM_BOT_TOKEN` — Bot Token
- `TELEGRAM_CHAT_ID` — Chat ID

</details>

<details>
<summary>🔔 Gotify / Bark</summary>

**Gotify:**
- `GOTIFY_URL` — 服务地址
- `GOTIFY_TOKEN` — 应用访问令牌
- `GOTIFY_PRIORITY` — 优先级（1-10，默认 9）

**Bark:**
- `BARK_KEY` — APP 打开即可看到
- `BARK_SERVER` — 自建服务器地址（可选，默认 `https://api.day.app`）

</details>

---

## 🔧 故障排除

| 现象 | 排查方向 |
| :--- | :--- |
| ❌ 401 错误 | cookie 已过期，重新登录后插件同步即可 |
| ⚠️ 502 / 连接超时 | 服务端暂时不可用，脚本会自动重试 |
| 🔀 路由到错误平台 | 检查 `PROVIDERS` secret；重新执行插件"同步所有账号" |
| 🍪 cookie 提取失败 | 确认已在浏览器中登录该站点 |
| 🔍 api_user 解析失败 | 确认站点为 NewAPI / OneAPI 架构 |
| 🆕 新平台全部 401 | `PROVIDERS` 未包含该平台，执行插件同步后重新触发 Actions |
| `Unexpected token '<'` / `HTTP 200: HTML returned instead of user JSON` | 用户信息接口返回 HTML（Cloudflare 验证页、登录页或 API 路由错误）。新版脚本会区分响应类型，不再把 HTML 当作 JSON 解析 |
| `Cloudflare verification HTML returned instead of user JSON` | GitHub 托管运行器出口网络可能被网站限制。先在已登录的普通浏览器确认站点可访问，再从有权使用且能访问该服务的运行环境执行；仅更换 Cookie 或重试不一定能解决 |
| `Login page returned instead of user JSON` | 登录态可能失效，重新登录网站，使用插件同步账号 Secret 后运行 |
| Xvfb / xkbcomp `Could not resolve keysym XF86...` | Ubuntu 键盘映射警告，与用户信息 API 返回 HTML 无关。工作流将其重定向，仅在 Xvfb 启动失败时显示 |

**注意：** `checkin.yml` 的 GitHub 托管运行器仍固定 `ubuntu-24.04`。Chromium 启动成功不代表网站已允许 GitHub 数据中心 IP 访问 API。仓库当前只保留手动 `workflow_dispatch`；如持续收到安全验证页面，请使用网站允许的执行环境（例如已获授权的自有服务器任务），或在浏览器中完成网站要求的验证。程序不会把无法核实的自动签到标记为成功，也不会自动绕过人工安全验证。新的 HTML 诊断不会打印页面源码、Cookie 或 Token。

---

## 🛠️ 本地开发

```bash
# 安装依赖
uv sync --dev

# 安装 Playwright 浏览器
uv run playwright install chromium

# 配置环境变量
cp .env.example .env  # 编辑 .env 填入账号信息

# 运行签到
uv run checkin.py

# 运行测试
uv run pytest tests/
uv run pytest tests/ --cov=. --cov-report=html
```

---

## 🤝 贡献指南

欢迎贡献！提交 PR 前请确保：

```bash
uv run pre-commit install
uv run ruff check . && uv run ruff format .
uv run mypy .
uv run pytest tests/ --cov=.
```

本项目使用 Ruff（代码风格）、MyPy（类型检查）、Bandit（安全扫描）、Pytest（测试）和 pre-commit 保证代码质量。

---

## 📝 更新日志

<details>
<summary><b>v1.9</b> — 2026-04-14 签到体验优化 + heibai 停用</summary>

- 🚫 **heibai 停用** — 账号因自动签到检测被封禁，代码已注释保留
- 📊 **通知频率优化** — 仅在余额变化、首次运行或全部失败时发送通知
- 📝 **通知格式精简** — 按状态分组，每账号一行，无变化账号折叠显示
- 🔐 **SSL 证书回退** — 自签名证书站点自动 `verify=False` 重试
- 🛡️ **Turnstile 自动检测** — 签到返回 Turnstile 要求时自动切换 Playwright
- 🐛 **错误信息透明化** — 不再显示 "Unknown error"，展示实际错误原因
- ⏱️ **Playwright 超时增加** — Cloudflare challenge 超时从 30s 增至 60s

</details>

<details>
<summary><b>v1.8</b> — 2026-04-06 Heibai 签到方案重构：纯 API + PoW 验证码</summary>

- 🔓 逆向发现 heibai 验证码是 **cap.js PoW**（SHA-256 工作量证明），不是 Cloudflare Turnstile
- 🚀 纯 Python HTTP 签到：challenge → solve → redeem → checkin，**无需浏览器**
- 🧹 移除 DrissionPage/WARP/Xvfb/Chrome 依赖，workflow 从 9 分钟降至 1 分钟
- 🔧 Chrome 扩展修复 heibai 单账号测试（dryRun 未传递的 bug）
- 📦 清理 ~460 行废弃代码（Turnstile solver、DrissionPage check-in）

</details>

<details>
<summary><b>v1.7</b> — 2026-03-17 网络异常自动重试</summary>

- 🔄 签到请求遇到 HTTP 5xx / 网络异常时自动重试（间隔 5 秒）
- 🔄 用户信息获取同样支持重试
- 📋 重试日志清晰标注 `[RETRY]`

</details>

<details>
<summary><b>v1.6</b> — 2026-03-17 插件一键注册新平台</summary>

- 🔌 插件同步时自动更新 `PROVIDERS` secret
- 🐛 修复新平台路由到 anyrouter 的 bug
- 🔑 签到脚本自动注册 provider（双重保险）
- 🐛 修复多账号同一平台去重 bug（改用 `(api_user, provider)` 组合键）
- 🏷️ 新增动态 provider tag 生成

</details>

<details>
<summary><b>v1.5</b> — 2026-03-12 Cookie 提取与 api_user 解析修复</summary>

- 🐛 修复 Cookie 竞态条件（两阶段提取）
- 🐛 修复 api_user 解析失败（优先 localStorage）
- 🐛 修复 tab 生命周期 bug

</details>

<details>
<summary><b>v1.4</b> — 2026-03-11 加密实现修复</summary>

- 🔐 修复 GitHub Secrets 加密 bug（改用 libsodium sealed box）
- 📦 Chrome 扩展引入 libsodium，替换 TweetNaCl

</details>

<details>
<summary><b>v1.3</b> — 2026-03-11 Secret 命名规范统一</summary>

- 🏷️ 统一格式为 `{api_user}_{PROVIDER}`

</details>

<details>
<summary><b>v1.2</b> — 2026-03-11 Tampermonkey 脚本 + 导入功能</summary>

- 🐒 新增油猴脚本，功能与 Chrome 扩展对等
- 📥 新增从 ANYROUTER_ACCOUNTS 一键导入

</details>

<details>
<summary><b>v1.1</b> — 2026-03-11 Chrome 扩展体验优化</summary>

- 🔄 双模式账号配置（列表 / JSON）
- 🔍 api_user 自动获取

</details>

<details>
<summary><b>v1.0</b> — 初始版本</summary>

- 🚀 多账号自动签到
- 📣 多渠道通知
- 🔑 ANYROUTER_ACCOUNT_* 独立管理
- 🧩 Chrome 扩展 AnyRouter Cookie Updater

</details>

---

## 📊 Star History

<a href="https://star-history.com/#shenhao-stu/anyrouter-check-in&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=shenhao-stu/anyrouter-check-in&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=shenhao-stu/anyrouter-check-in&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=shenhao-stu/anyrouter-check-in&type=Date" />
 </picture>
</a>

---

## ⚖️ 免责声明

本脚本仅用于学习和研究目的，使用前请确保遵守相关网站的使用条款。

---

<!-- English Documentation -->

<div align="center">

# 🌍 English Documentation

</div>

## ✨ Features

- 🌐 **Multi-platform** — Compatible with all NewAPI / OneAPI sites
- 👥 **Multi-account** — Check in multiple accounts on the same platform simultaneously
- 🔌 **One-click onboarding** — Chrome extension / Tampermonkey auto-registers new platforms
- 🔄 **Auto-retry** — Retries on 5xx / network timeouts
- 🛡️ **WAF bypass** — Playwright auto-fetches WAF cookies
- 📣 **Multi-channel notifications** — Feishu / DingTalk / WeCom / Telegram / Email / Bark / Gotify / PushPlus
- ⏰ **Scheduled execution** — GitHub Actions runs every 6 hours

> Built-in support for [AnyRouter](https://anyrouter.top/register?aff=gSsN) and [AgentRouter](https://agentrouter.org). Other platforms are onboarded via the browser extension or `PROVIDERS` secret.

## 🚀 Quick Start

### 1️⃣ Fork this repository

### 2️⃣ Install the browser extension & configure GitHub PAT

Use the **Chrome extension** or **Tampermonkey userscript** to auto-sync cookies.

1. Create a [Fine-grained PAT](https://github.com/settings/personal-access-tokens) scoped to your repository. Use **Environments: Read and write** for the `production` Environment (or **Secrets: Read and write** when the Environment field is blank and the extension uploads Repository Secrets). A classic PAT instead requires `repo` scope.
2. Enter the token in the extension settings

### 3️⃣ Add accounts in the extension

```json
[
  { "domain": "https://anyrouter.top" },
  { "domain": "https://agentrouter.org" }
]
```

The extension automatically:
- 🍪 Extracts `session` cookie from the browser
- 🔍 Resolves `api_user` via `/api/user/self`
- 🔑 Pushes `ANYROUTER_ACCOUNT_{api_user}_{PROVIDER}` secret
- 📦 Updates `PROVIDERS` secret to register new platforms

### 4️⃣ Set up Environment Secret (first time only)

1. Go to **Settings → Environments** → create `production`
2. Add secret `ANYROUTER_ACCOUNTS` (JSON array, or `[]` if using individual secrets)

### 5️⃣ Enable GitHub Actions

Enable the "AnyRouter 自动签到" workflow and trigger a manual run to verify.

## 📋 Account Configuration

### Individual Account Secrets (Recommended)

Each account gets its own secret:

```
ANYROUTER_ACCOUNT_{api_user}_{PROVIDER}
```

Secret value format:
```json
{
  "cookies": { "session": "session_value" },
  "api_user": "760",
  "provider": "computetoken",
  "domain": "https://computetoken.ai"
}
```

### Custom Providers

Add a `PROVIDERS` environment secret:

```json
{
  "computetoken": { "domain": "https://computetoken.ai" },
  "freestyle": { "domain": "https://api.freestyle.cc.cd" }
}
```

Standard new-api / one-api sites use default paths (`/api/user/self`, `/api/user/sign_in`, with automatic fallback to `/api/user/checkin` on 404).

## 📣 Notifications

Configure notification channels via environment secrets:

| Channel | Required Secrets |
| :--- | :--- |
| 📧 Email (SMTP) | `EMAIL_USER`, `EMAIL_PASS`, `EMAIL_TO` |
| 🤖 DingTalk | `DINGDING_WEBHOOK` |
| 🐦 Feishu (Lark) | `FEISHU_WEBHOOK` |
| 💬 WeCom | `WEIXIN_WEBHOOK` |
| 📱 PushPlus | `PUSHPLUS_TOKEN` |
| 📱 Server Chan | `SERVERPUSHKEY` |
| ✈️ Telegram | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |
| 🔔 Gotify | `GOTIFY_URL`, `GOTIFY_TOKEN` |
| 🔔 Bark | `BARK_KEY` |

## 🔧 Troubleshooting

| Issue | Solution |
| :--- | :--- |
| ❌ HTTP 401 | Cookie expired — re-login and let the extension sync |
| ⚠️ 502 / timeout | Server temporarily unavailable, auto-retry handles this |
| 🔀 Wrong platform | Check `PROVIDERS` secret; re-run extension "Sync All" |
| 🆕 New platform 401 | `PROVIDERS` missing — run extension sync, then re-trigger Actions |

## 🛠️ Local Development

```bash
uv sync --dev
uv run playwright install chromium
uv run checkin.py

# Tests
uv run pytest tests/
```

---

<div align="center">

Made with ❤️ by [shenhao-stu](https://github.com/shenhao-stu)

</div>


