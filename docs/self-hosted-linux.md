# 自有 Ubuntu Linux 服务器运行 AnyRouter / AgentRouter 签到

本说明适用于已经获得网站授权、允许自动化访问的 Ubuntu 24.04 x64 服务器。
GitHub-hosted Runner 无法访问某个受 Cloudflare 保护的网站，并不意味着更换服务器后一定成功。
如果网站要求人工验证，须遵守网站要求；不能把验证页视为签到成功。

## 1. 安装 Linux 运行依赖

通过 SSH 使用普通 Linux 账户登录服务器。服务器不需要显示器或桌面环境。

    sudo apt-get update
    sudo apt-get install -y ca-certificates curl git xvfb xauth

当前 Python 代码通过 Playwright 启动 headless=False 的 Chromium。Linux 无桌面服务器
需要 Xvfb 提供虚拟 X11 显示（通过 xvfb-run 启动），不能假定 headless=True 是等价替代。
xauth 为 xvfb-run 所需依赖。键盘映射里的 XF86 警告通常不影响浏览器使用。

## 2. 获取项目，安装 uv / Python 3.11 / Chromium

    mkdir -p "$HOME/apps"
    cd "$HOME/apps"
    git clone https://github.com/lic-twrightjay/anyrouter-check-in.git
    cd anyrouter-check-in

    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    uv python install 3.11
    uv sync --frozen --python 3.11
    uv run --frozen playwright install --with-deps chromium

最后一条命令同时检查 Chromium 所需 Linux 库，必要时会要求输入 sudo 密码。
--frozen 使用当前仓库的 uv.lock，避免部署时改动锁文件。首次安装须联网；
执行后应看到 Chromium 安装成功。浏览器版本由 Playwright 依赖决定。

## 3. 在服务器上安全配置登录账号

GitHub Environment / Repository Secret 无法通过 API 再读取其明文。
服务器必须从本人已登录的浏览器或其他安全凭据存储中获取自己的 session Cookie。
Cookie 和 PAT 均属于登录凭据，不要发送到聊天、Issues、公开日志或 Git 仓库。

    cd "$HOME/apps/anyrouter-check-in"
    umask 077
    cp .env.example .env
    chmod 600 .env
    nano .env

用以下示例代替 .env 的原有 ANYROUTER_ACCOUNTS 行：

    ANYROUTER_ACCOUNTS='[{"cookies":{"session":"REPLACE_WITH_OWN_SESSION"},"api_user":"356997","provider":"agentrouter","domain":"https://agentrouter.org"}]'

示例中的 ID 356997 仅对应之前用户提供的测试信息，应自行核实。
将 REPLACE_WITH_OWN_SESSION 替换为该账号有效的 Cookie；多个账号可写在同一 JSON 数组中。
对于内置 agentrouter 平台，不需要额外设置 PROVIDERS。
仓库已在 .gitignore 中排除 .env，仍须保持文件权限为 600。
Chrome 插件同步 GitHub Secrets 不会自动更新自有服务器上的 .env。

可先校验账号配置，仅输出账号数量，不输出 Cookie 值：

    uv run --frozen python -c 'from utils.config import load_accounts_config; print("Accounts loaded:", len(load_accounts_config() or []))'

## 4. 使用虚拟显示启动 Chromium，执行一次签到

    cd "$HOME/apps/anyrouter-check-in"
    bash scripts/run-linux.sh

脚本自动定位项目根目录，检查 uv 和 xvfb-run，然后执行：

    xvfb-run -a -s '-screen 0 1920x1080x24 -nolisten tcp' uv run --frozen python -u checkin.py

xvfb-run -a 会自动选取未占用的 DISPLAY，避免固定端口 :99 冲突。
若登录失败，先在普通浏览器核实账号是否有效，再检查服务器是否被网站允许访问。
任何 HTTP 200 的 HTML 验证页都不能视为签到成功。
可选 CHECKIN_PROXY / HTTPS_PROXY / HTTP_PROXY 仅用于经网站允许的网络或代理场景；
配置代理不保证能解除网站的访问限制。

## 5. 手动执行成功以后再启用 cron

先确认该服务器手动运行确实得到了用户信息和签到成功结果。
随后运行 crontab -e，加入以下一行（将 YOUR_USER 换成真正的 Linux 用户名）：

    15 8 * * * /usr/bin/flock -n /tmp/anyrouter-checkin-YOUR_USER.lock /bin/bash /home/YOUR_USER/apps/anyrouter-check-in/scripts/run-linux.sh >> /home/YOUR_USER/apps/anyrouter-check-in/checkin.log 2>&1

此示例按服务器本地时间每天 08:15 运行，并通过 flock 避免重叠任务。
若要按北京时间运行，请核对服务器时区；必要时由管理员设置 Asia/Shanghai。
启用前创建并限制日志权限：

    touch "$HOME/apps/anyrouter-check-in/checkin.log"
    chmod 600 "$HOME/apps/anyrouter-check-in/checkin.log"
    date
    crontab -l

cron 的默认 PATH 较短，run-linux.sh 会主动将 $HOME/.local/bin 加入 PATH，
但如果 uv 安装在其它位置，应相应调整脚本。日志可能含有服务端错误信息，
不应公开或未经筛查直接分享。

## 6. 版本更新与故障排查

    cd "$HOME/apps/anyrouter-check-in"
    git pull --ff-only
    uv sync --frozen --python 3.11
    uv run --frozen playwright install --with-deps chromium
    bash scripts/run-linux.sh

| 现象 | 检查方法 |
| --- | --- |
| xvfb-run 找不到 xauth | sudo apt-get install -y xauth |
| Chromium 启动时缺少共享库 | 重新执行 Playwright 的 install --with-deps chromium |
| Loaded 0 account(s) | 检查 .env JSON、账号 Cookie 和当前目录 |
| Login page / 401 | session 可能已过期，重新登录并更新 .env |
| Cloudflare verification HTML | 核实网站是否允许该服务器访问，以及是否需人工验证；不能宣称签到成功 |
| HTTP 200 非 JSON | 检查 API 地址或登录状态，新版停止此类确定性错误的无意义重试 |
| HTTP 5xx / 短暂网络断开 | 脚本保留限次重试，无法保证每次请求都恢复 |

此文档提供可操作部署方案；除非在目标服务器看到真实成功证据，否则不代表
自有服务器已完成验收。
