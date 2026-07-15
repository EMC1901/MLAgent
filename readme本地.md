# MLAgent Windows 本地部署与使用指南

本文档面向编程开发新手，介绍如何在 Windows 电脑上下载、安装、部署并使用 MLAgent。

本文采用的部署方式与当前开发电脑一致：

- React 前端直接运行在 Windows 本机；
- FastAPI 后端直接运行在 Windows 本机；
- PostgreSQL 数据库运行在 Docker 容器中；
- 浏览器访问本机前端和后端；
- 不使用 `docker-compose.prod.yml`，也不使用 Docker 运行前端和后端。

请从上到下按顺序操作。每一步都写明了“为什么做”和“怎样算完成”。如果某一步没有完成，不建议直接跳到下一步。

## 1. 先了解最终运行结构

系统启动后的关系如下：

```text
浏览器
  │
  ├── http://localhost:3000
  │       │
  │       └── React 前端（Windows 本机 Node.js 进程）
  │                    │
  │                    └── http://localhost:8000
  │                              │
  │                              └── FastAPI 后端（Windows 本机 Python 进程）
  │                                           │
  │                                           └── localhost:5432
  │                                                     │
  │                                                     └── PostgreSQL 16（Docker 容器）
  │
  └── http://localhost:8000/health（后端健康检查）
```

各部分的作用：

| 部分 | 运行位置 | 作用 | 端口 |
| --- | --- | --- | --- |
| 前端 | Windows 本机 | 显示操作页面、接收用户操作 | 3000 |
| 后端 | Windows 本机 | 处理任务、调用模型、训练和生成结果 | 8000 |
| PostgreSQL | Docker | 保存任务、配置和流程结果 | 5432 |
| 上传文件和产物 | Windows `C:\app` | 保存数据集、中间产物、模型和最终结果 | 不使用端口 |

完整部署成功需要同时满足：

1. Docker 中的 PostgreSQL 显示为 `healthy`；
2. 后端 PowerShell 窗口正在运行 uvicorn；
3. <http://localhost:8000/health> 返回 `{"status":"ok"}`；
4. 前端 PowerShell 窗口显示 `Compiled successfully!`；
5. <http://localhost:3000> 可以打开 MLAgent 页面。

## 2. 安装前的准备

### 2.1 电脑配置建议

建议使用：

- 64 位 Windows 10 或 Windows 11；
- 至少 8 GB 内存，推荐 16 GB 或更多；
- 至少 15 GB 可用磁盘空间；
- 能够访问 GitHub、Docker Hub、npm 和 Python 软件源的网络；
- Chrome、Edge 或 Firefox 浏览器。

机器学习训练、材料特征计算和依赖安装会消耗较多 CPU、内存、磁盘和网络资源。第一次建议使用小数据集验证流程。

### 2.2 准备三个 PowerShell 窗口

系统运行时建议准备三个 PowerShell 窗口：

| 窗口 | 用途 | 是否需要一直保持打开 |
| --- | --- | --- |
| PowerShell 1 | 管理 Docker PostgreSQL | 启动完成后可以关闭 |
| PowerShell 2 | 运行 Python 后端 | 系统使用期间必须保持打开 |
| PowerShell 3 | 运行 React 前端 | 系统使用期间必须保持打开 |

不要在同一个 PowerShell 中先运行后端再运行前端，因为后端启动后会持续占用该窗口。

## 3. 安装 Git

Git 用来从 GitHub 下载代码和获取后续更新。

### 3.1 下载并安装

1. 打开 <https://git-scm.com/downloads>；
2. 下载 Windows 版本；
3. 运行安装程序；
4. 如果不了解各安装选项，保持默认设置；
5. 安装完成后，关闭并重新打开 PowerShell。

### 3.2 验证 Git

执行：

```powershell
git --version
```

完成标准：看到类似内容：

```text
git version 2.x.x.windows.x
```

如果提示“无法将 git 识别为命令”，说明 Git 没有正确安装，或者安装后没有重新打开 PowerShell。

## 4. 安装 Python 3.12

后端 Dockerfile 使用 Python 3.12，因此 Windows 本地后端也推荐使用 Python 3.12。不要优先使用尚未验证的新版本 Python。

### 4.1 下载并安装

1. 打开 <https://www.python.org/downloads/windows/>；
2. 下载 Python 3.12 的 64 位 Windows installer；
3. 运行安装程序；
4. 勾选 **Add python.exe to PATH**；
5. 完成安装。

### 4.2 验证 Python

重新打开 PowerShell，执行：

```powershell
py -3.12 --version
```

完成标准：显示类似：

```text
Python 3.12.x
```

还可以执行：

```powershell
py -0p
```

该命令会列出电脑中所有 Python。确认列表中存在 Python 3.12。

## 5. 安装 Node.js

Node.js 用来安装和运行 React 前端。

### 5.1 下载并安装

1. 打开 <https://nodejs.org/>；
2. 下载 64 位 Windows LTS 版本；
3. 推荐使用 Node.js 20 LTS；项目在 Node.js 22 环境中也可以运行；
4. 按默认选项完成安装；
5. 关闭并重新打开 PowerShell。

### 5.2 验证 Node.js 和 npm

执行：

```powershell
node --version
npm --version
```

完成标准：两个命令都能显示版本号。例如：

```text
v20.x.x
10.x.x
```

npm 会随 Node.js 一起安装，不需要单独下载。

## 6. 安装并启动 Docker Desktop

在本部署方式中，Docker 只负责运行 PostgreSQL 数据库。

### 6.1 安装 Docker Desktop

1. 打开 <https://www.docker.com/products/docker-desktop/>；
2. 下载 Windows 版本；
3. 完成安装；
4. 如果安装程序要求启用 WSL 2，请按照提示操作；
5. 必要时重启电脑；
6. 启动 Docker Desktop；
7. 等待 Docker Engine 显示为 Running。

### 6.2 验证 Docker

打开新的 PowerShell，执行：

```powershell
docker --version
docker compose version
docker info
```

完成标准：

- `docker --version` 显示 Docker 版本；
- `docker compose version` 显示 Compose 版本；
- `docker info` 能显示 Server 信息；
- 没有 `Cannot connect to the Docker daemon`；
- 没有“找不到 Docker Desktop Linux Engine”错误。

如果前两个命令成功而 `docker info` 失败，通常是 Docker Desktop 尚未启动完成。

## 7. 下载 MLAgent 代码

### 7.1 使用 Git 下载（推荐）

先选择保存项目的位置。例如在 `C:\projects` 下保存：

```powershell
cd C:\projects
git clone https://github.com/EMC1901/MLAgent.git
cd MLAgent
```

为什么推荐 Git：以后可以执行 `git pull` 获取更新，也能清楚看到本地修改。

执行：

```powershell
Get-ChildItem
```

完成标准：至少看到：

```text
backend
frontend
docker-compose.yml
docker-compose.prod.yml
```

此时所在目录称为“项目根目录”。后文中的数据库命令都要在这里运行。

### 7.2 使用 ZIP 下载

如果暂时不使用 Git：

1. 打开项目 GitHub 页面；
2. 单击 **Code**；
3. 单击 **Download ZIP**；
4. 将 ZIP 完整解压；
5. 进入解压后的 `MLAgent-main` 文件夹；
6. 在文件夹空白处按住 Shift 并单击鼠标右键；
7. 选择“在终端中打开”；
8. 执行 `Get-ChildItem` 检查文件。

不能直接在 ZIP 压缩包预览窗口里运行项目。

## 8. 只在 Docker 中启动 PostgreSQL

这是本部署方式最重要的区别：只启动 `db`，不要启动 Docker 中的 backend 和 frontend。

### 8.1 启动数据库

确保 PowerShell 位于项目根目录，然后执行：

```powershell
docker compose up -d db
```

命令含义：

- `docker compose`：读取项目根目录中的 `docker-compose.yml`；
- `up`：创建并启动服务；
- `-d`：让数据库在后台运行；
- `db`：只启动 PostgreSQL 数据库服务。

> 不要执行不带 `db` 的 `docker compose up -d`。否则 Compose 还会启动 Docker 版前端和后端，占用 3000 和 8000 端口，与 Windows 本地进程冲突。

第一次执行时，Docker 会下载 `postgres:16-alpine` 镜像，需要等待网络下载完成。

### 8.2 检查数据库状态

执行：

```powershell
docker compose ps db
```

完成标准：db 服务状态为 `Up` 或 `running`，并显示 `healthy`。

还可以执行 PostgreSQL 自带检查：

```powershell
docker compose exec db pg_isready -U postgres -d mlagent
```

完成标准：出现：

```text
accepting connections
```

当前开发数据库配置为：

| 配置 | 值 |
| --- | --- |
| 地址 | `localhost` |
| 端口 | `5432` |
| 数据库 | `mlagent` |
| 用户名 | `postgres` |
| 开发密码 | `postgres` |

这些默认账号密码只适合本机开发，不能直接用于公网生产环境。

### 8.3 数据保存在哪里

数据库数据保存在 Docker volume `mlagent_postgres_data` 中。停止或重建 db 容器时，数据通常仍会保留。

普通停止数据库：

```powershell
docker compose stop db
```

以后重新启动：

```powershell
docker compose up -d db
```

不要随意执行 `docker compose down -v`。其中 `-v` 会删除数据库 volume，历史任务和数据库数据将永久丢失。

## 9. 创建 Windows 本地产物目录

项目中的部分上传和模型产物路径使用 `/app/...`。在当前 Windows 本地后端运行方式中，这些路径对应 `C:\app\...`。

打开普通 PowerShell，执行：

```powershell
New-Item -ItemType Directory -Force -Path C:\app\uploads
New-Item -ItemType Directory -Force -Path C:\app\artifacts
```

为什么要创建：后端会在这里保存上传的数据集、特征、训练产物、解释性分析和最终输出。如果目录不存在或当前用户不能写入，流程可能在中途失败。

检查目录：

```powershell
Get-ChildItem C:\app
```

完成标准：看到 `uploads` 和 `artifacts` 两个文件夹。

如果提示“拒绝访问”：

1. 关闭当前 PowerShell；
2. 在开始菜单搜索 PowerShell；
3. 右键选择“以管理员身份运行”；
4. 再执行上面的 `New-Item` 命令；
5. 确保当前 Windows 用户有修改目录的权限。

必要时可在管理员 PowerShell 中授予当前用户修改权限：

```powershell
icacls C:\app /grant "$($env:USERNAME):(OI)(CI)M" /T
```

完成后关闭管理员 PowerShell。日常运行前后端不建议使用管理员权限。

## 10. 安装并配置 Windows 本地后端

以下操作在 PowerShell 2 中执行。

### 10.1 进入 backend 目录

假设项目位于 `C:\projects\MLAgent`：

```powershell
cd C:\projects\MLAgent\backend
```

检查：

```powershell
Get-ChildItem
```

完成标准：看到 `app`、`requirements.txt`、`alembic.ini` 和 `.env.example`。

### 10.2 创建 Python 虚拟环境

执行：

```powershell
py -3.12 -m venv .venv
```

为什么要使用虚拟环境：不同项目可能需要不同版本的 Python 包。`.venv` 可以把 MLAgent 的依赖与电脑全局 Python 隔离，避免相互影响。

完成标准：backend 目录中出现 `.venv` 文件夹，并且命令没有报错。

### 10.3 激活虚拟环境

执行：

```powershell
.\.venv\Scripts\Activate.ps1
```

完成标准：PowerShell 提示符前出现 `(.venv)`，例如：

```text
(.venv) PS C:\projects\MLAgent\backend>
```

如果出现“禁止运行脚本”错误，在当前 PowerShell 中执行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

`-Scope Process` 只对当前 PowerShell 窗口生效，关闭窗口后会恢复，不会永久修改全局执行策略。

### 10.4 升级 pip 安装工具

执行：

```powershell
python -m pip install --upgrade pip setuptools wheel
```

为什么要做：较新的安装工具更容易找到 Python 3.12 对应的预编译包，减少安装失败。

完成标准：命令最后出现 `Successfully installed`，或者提示已经是最新版本。

### 10.5 安装后端依赖

执行：

```powershell
python -m pip install -r requirements.txt
```

项目包含 pandas、scikit-learn、pymatgen、matminer、xgboost、lightgbm 等依赖，下载和安装可能需要较长时间。不要在命令仍在下载时关闭窗口。

完成标准：命令正常回到 `(.venv)` 提示符，并且末尾没有红色 `ERROR`。

安装后执行导入检查：

```powershell
python -c "import fastapi, uvicorn, sqlmodel, pandas, pymatgen, matminer; print('Backend dependencies: OK')"
```

完成标准：显示：

```text
Backend dependencies: OK
```

### 10.6 创建后端 `.env`

确保当前仍位于 backend 目录，执行：

```powershell
Copy-Item .env.example .env
```

为什么要做：`.env` 告诉本地后端连接 Windows 的 `localhost:5432`，而不是连接 Docker 网络中的主机名 `db`。

用记事本打开：

```powershell
notepad .env
```

确保至少包含：

```dotenv
APP_NAME=MLAgent
APP_ENV=development
DEBUG=True
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/mlagent
CORS_ORIGINS=["http://localhost:3000"]

DATASET_UPLOAD_DIR=C:/app/uploads
FEATURE_ARTIFACT_DIR=C:/app/artifacts/features
MODEL_READY_ARTIFACT_DIR=C:/app/artifacts/model_ready
```

说明：

- `localhost` 表示后端连接本机暴露的 Docker PostgreSQL 端口；
- `postgres:postgres` 是本地开发数据库用户名和密码；
- `CORS_ORIGINS` 允许本机 3000 端口的前端访问后端；
- 路径使用正斜杠，避免 Windows 反斜杠转义问题；
- `.env` 只能保存在本机，不能上传到 GitHub。

保存并关闭记事本。

检查文件是否存在：

```powershell
Test-Path .env
```

完成标准：显示 `True`。

### 10.7 启动后端

启动前确认：

- PowerShell 提示符前有 `(.venv)`；
- 当前目录是 backend；
- Docker PostgreSQL 已经显示 `healthy`；
- backend 目录中存在 `.env`。

执行：

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

命令含义：

- `app.main:app`：加载 `backend/app/main.py` 中的 FastAPI 应用；
- `--reload`：本地开发时修改 Python 文件后自动重启后端；
- `--host 127.0.0.1`：只允许当前电脑访问；
- `--port 8000`：后端使用 8000 端口。

第一次连接全新数据库时，后端会根据模型创建数据库表。

完成标准：日志中出现类似：

```text
Uvicorn running on http://127.0.0.1:8000
Application startup complete
```

不要关闭这个 PowerShell 窗口。

### 10.8 验证后端

打开浏览器访问：

<http://localhost:8000/health>

正常结果：

```json
{"status":"ok"}
```

也可以新开 PowerShell 执行：

```powershell
Invoke-RestMethod http://localhost:8000/health
```

看到 `status : ok`，说明 Windows 本地后端已成功运行并可以接收请求。

## 11. 安装并运行 Windows 本地前端

以下操作在 PowerShell 3 中执行。不要关闭正在运行后端的 PowerShell 2。

### 11.1 进入 frontend 目录

```powershell
cd C:\projects\MLAgent\frontend
```

如果项目位于其他位置，请使用自己的实际路径。

执行：

```powershell
Get-ChildItem
```

完成标准：看到 `src`、`public`、`package.json` 和 `package-lock.json`。

### 11.2 安装前端依赖

执行：

```powershell
npm ci --legacy-peer-deps
```

为什么不能只执行普通的 `npm install`：当前项目使用 `react-scripts 5` 和 TypeScript 5，新版 npm 会报告 peer dependency 冲突。`--legacy-peer-deps` 是当前项目所需的兼容安装参数。

为什么使用 `npm ci`：它按照 `package-lock.json` 安装锁定版本，使不同开发者得到更一致的依赖。

第一次安装会下载大量 npm 包，可能需要数分钟。

完成标准：

- 命令最后没有 `npm ERR!`；
- frontend 目录中出现 `node_modules`；
- 看到 deprecated warning 不代表安装失败，只要没有 `npm ERR!` 即可。

检查：

```powershell
Test-Path node_modules\react-scripts
```

完成标准：显示 `True`。

### 11.3 启动前端

执行：

```powershell
npm start
```

第一次编译可能需要几十秒。React 可能自动打开浏览器。

完成标准：PowerShell 出现：

```text
Compiled successfully!
Local: http://localhost:3000
```

不要关闭这个 PowerShell 窗口。关闭后，前端页面将无法访问。

### 11.4 验证前端

浏览器打开：

<http://localhost:3000>

完成标准：

- 能看到 Mat-AIDE/MLAgent 页面；
- 页面顶部存在 **Load Historical Tasks** 和 **Switch Model**；
- 页面没有一直空白或持续加载；
- 浏览器控制台没有持续出现无法连接 `localhost:8000` 的错误。

## 12. 每次日常使用时如何启动

完成首次安装后，以后不需要每天重复安装依赖。按照以下顺序启动即可。

### 第一步：启动 Docker Desktop

等待 Docker Engine 运行完成。

### 第二步：启动 PostgreSQL

PowerShell 1：

```powershell
cd C:\projects\MLAgent
docker compose up -d db
docker compose ps db
```

完成标准：db 为 `healthy`。

### 第三步：启动后端

PowerShell 2：

```powershell
cd C:\projects\MLAgent\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

如果激活脚本被阻止：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

完成标准：<http://localhost:8000/health> 返回 `{"status":"ok"}`。

### 第四步：启动前端

PowerShell 3：

```powershell
cd C:\projects\MLAgent\frontend
npm start
```

完成标准：出现 `Compiled successfully!`，并能打开 <http://localhost:3000>。

### 第五步：保持两个运行窗口

使用系统期间：

- 不要关闭后端 PowerShell；
- 不要关闭前端 PowerShell；
- Docker Desktop 必须保持运行；
- 可以关闭用于启动数据库的 PowerShell 1，因为数据库在后台容器中运行。

## 13. 首次使用前准备数据集

系统支持：

- `.csv`
- `.xlsx`
- `.xls`

默认单个文件最大 100 MB。第一次建议使用较小的数据集。

上传前检查：

1. 第一行是列名；
2. 每个列名唯一；
3. 每行代表一个样本；
4. 不使用合并单元格；
5. 文件中存在预测目标列；
6. 目标列名称必须与创建任务时填写的 Target Column 完全一致；
7. 回归任务目标列通常是数值；
8. 分类任务目标列是类别标签；
9. 删除完全空白的行列和额外说明标题。

简单回归数据示例：

```csv
composition,band_gap
Si,1.12
GaAs,1.42
ZnO,3.37
```

这个例子中：

- 输入列是 `composition`；
- 目标列是 `band_gap`；
- Input Type 应选择 `Chemical composition`；
- Task Type 应选择 `Regression`；
- Target Column 必须填写 `band_gap`。

## 14. 配置大语言模型

部分流程需要调用兼容 OpenAI Chat Completions 的模型接口。没有配置模型时，前后端可以启动，但 AI 解释、规划和分析步骤无法完整执行。

### 14.1 准备模型信息

需要准备：

- 模型名称，例如 `qwen-plus`；
- 模型服务商提供的 API Key；
- Base URL，例如 `https://dashscope.aliyuncs.com/compatible-mode/v1`。

API Key 相当于密码，不能上传到 GitHub、写入 README、发送截图或分享给其他人。

### 14.2 在页面中配置

1. 打开 <http://localhost:3000>；
2. 单击 **Switch Model**；
3. 填写 Model Name；
4. 填写 API Key；
5. 填写 Base URL；
6. 根据模型情况决定是否启用 thinking；
7. 保存配置；
8. 等待系统发送测试请求。

完成标准：页面提示连接成功，模型名称正确，API Key 以掩码显示。

常见模型接口错误：

| 错误 | 常见原因 |
| --- | --- |
| 401 | API Key 错误或过期 |
| 403 | 账号没有模型权限 |
| 404 | 模型名称或 Base URL 错误 |
| 429 | 额度不足或调用频率过高 |
| timeout | 网络无法访问服务商或模型响应过慢 |

页面设置的模型配置保存在当前后端进程内存中。后端重启后可能需要重新配置。

如果希望通过 `.env` 配置默认模型，可以在 `backend/.env` 中增加：

```dotenv
LLM_PROVIDER=dashscope
LLM_MODEL=qwen-plus
LLM_API_KEY=<填写自己的真实API Key>
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_TIMEOUT=480
```

保存后需要停止并重新启动后端。真实 `.env` 不能提交到 GitHub。

## 15. 创建并运行第一个任务

### 15.1 填写 Task Specification

打开 <http://localhost:3000>。首次进入时会看到任务表单。

| 字段 | 填写内容 | 示例 |
| --- | --- | --- |
| Task Name | 任务名称 | `Band gap prediction` |
| Task Description | 希望解决的问题 | `根据材料化学组成预测实验带隙` |
| Material System | 材料体系 | `Semiconductors` |
| Dataset Description | 数据来源、规模和主要列 | `包含化学式和实验带隙的数据集` |
| Input Type | 输入类型 | `Chemical composition` |
| Target Column | 文件中目标列的准确名称 | `band_gap` |
| Prediction Target | 预测目标 | `experimental band gap` |
| Task Type | 回归或分类 | `Regression` |
| Evaluation Metric | 评价指标 | `MAE` 或 `RMSE` |
| User Priority | 准确性、解释性、速度或稳健性 | `Accuracy`、`Interpretability` |
| Constraints | 额外限制，每行一条 | `Use interpretable models only` |

Dataset Description、Input Type、Target Column、Prediction Target 和 Task Type 是必填项。

填写后单击 **Submit Task Specification**。

完成标准：

- 没有红色错误；
- 系统生成 task ID；
- 左侧出现工作流菜单；
- 菜单从 Task Specification 一直到 Final Output。

### 15.2 按顺序运行完整流程

必须按照左侧菜单从上到下执行。每一步完成后再进入下一步。

| 顺序 | 菜单 | 操作 | 完成标准 |
| --- | --- | --- | --- |
| 1 | Task Specification | 检查任务字段 | 信息与数据集一致 |
| 2 | Task Interpretation | 单击 **Run Interpretation** | 显示系统对任务、目标和约束的解释 |
| 3 | Dataset Profile | 上传数据文件，然后单击 **Run Dataset Profiling** | 显示列信息、目标统计和质量检查 |
| 4 | Workflow Plan | 单击 **Run Workflow Planning** | 生成特征、预处理、模型和验证策略 |
| 5 | Feature Engineering | 单击 **Run Feature Engineering** | 显示生成特征和质量结果 |
| 6 | Data Preprocessing | 单击 **Run Data Preprocessing** | 生成可以训练的数据和预处理产物 |
| 7 | Model Search Plan | 单击 **Run Context Update** | 显示候选模型、HPO 和验证策略 |
| 8 | Pipeline Generation | 单击 **Generate Pipeline** | 生成可执行训练管线 |
| 9 | Pipeline Execution | 单击 **Run Training** | 训练完成并显示试验结果 |
| 10 | Metric Evaluation | 单击 **Run Metric Evaluation** | 显示模型排名和评估指标 |
| 11 | Iteration Decision | 单击 **Run Iteration Decision** | 给出停止或继续迭代的建议 |
| 12 | Interpretability | 单击 **Run Interpretability Analysis** | 显示特征重要性和解释结果 |
| 13 | Visualization | 查看并按需导出图表 | 图表能够正常显示 |
| 14 | Final Output | 单击 **Generate Final Output** | 显示 Ready 并下载最终 ZIP 包 |

每一步运行时：

- 等待按钮结束加载；
- 等待结果区域出现内容；
- 确认没有红色错误；
- 不要连续重复点击按钮；
- 长时间任务可以查看后端 PowerShell 中的实时日志；
- LLM、特征计算和模型训练可能需要数分钟。

如果某一步失败，先保存页面错误内容，然后查看后端 PowerShell 最后的错误和 Traceback。不要在上一步失败时继续下一步。

### 15.3 上传数据集

进入 **Dataset Profile**：

1. 在 Upload Dataset 区域单击选择文件，或把文件拖入上传框；
2. 等待 `Uploading...` 消失；
3. 确认页面显示上传文件名和预览；
4. 单击 **Run Dataset Profiling**；
5. 等待数据分析完成。

完成标准：页面显示数据规模、字段、目标列、缺失值或其他质量检查结果。

上传后的文件位于 `C:\app\uploads`。运行产物主要位于 `C:\app\artifacts`。

### 15.4 处理迭代建议

Iteration Decision 可能建议停止，也可能建议继续优化。

如果建议停止：

1. 阅读停止理由；
2. 继续运行 Interpretability；
3. 查看 Visualization；
4. 生成 Final Output。

如果显示 **Adopt & Rerun**：

1. 阅读 Revised Plan；
2. 阅读 Rerun Plan；
3. 确认准备从哪个阶段重新运行；
4. 单击 **Adopt & Rerun**；
5. 等待 Rerun Progress 中各步骤完成；
6. 再次运行 Iteration Decision 检查新结果。

不要不看计划就连续多次迭代。训练和 LLM 请求可能消耗较多时间和 API 费用。

### 15.5 查看历史任务

单击页面顶部 **Load Historical Tasks**：

- 单击任务行：打开历史任务；
- 单击 **Refresh**：刷新列表；
- 单击 **+ New Task**：新建任务。

数据库容器和 volume 未被删除时，历史任务会保留。

## 16. 正常停止系统

停止顺序建议为前端、后端、数据库。

### 16.1 停止前端

切换到运行 `npm start` 的 PowerShell 3，按：

```text
Ctrl+C
```

如果询问是否终止批处理作业，输入 `Y` 并回车。

完成标准：PowerShell 回到可以输入命令的提示符，<http://localhost:3000> 不再访问。

### 16.2 停止后端

切换到运行 uvicorn 的 PowerShell 2，按：

```text
Ctrl+C
```

完成标准：日志显示应用关闭，PowerShell 回到 `(.venv)` 提示符。

退出虚拟环境可以执行：

```powershell
deactivate
```

### 16.3 停止 PostgreSQL

在项目根目录执行：

```powershell
docker compose stop db
```

完成标准：

```powershell
docker compose ps db
```

不再显示运行中的 db，数据库数据仍保存在 volume 中。

如果经常使用系统，也可以让数据库容器继续运行；但 Docker Desktop 必须保持开启并占用一定系统资源。

## 17. 更新 GitHub 代码

使用 Git 克隆时，在项目根目录执行：

```powershell
git status
git pull
```

先执行 `git status` 是为了确认自己是否修改了文件。如果 `git pull` 提示冲突，不要直接删除本地文件，应请有经验的开发者协助处理。

更新后根据变化执行：

后端依赖可能变化：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

前端依赖可能变化：

```powershell
cd ..\frontend
npm ci --legacy-peer-deps
```

数据库配置可能变化：

```powershell
cd ..
docker compose up -d db
```

完成后按照第 12 节重新启动系统。

## 18. 常见问题排查

### 18.1 Docker 数据库无法启动

执行：

```powershell
docker info
docker compose logs --tail=200 db
```

常见原因：

- Docker Desktop 未启动；
- Docker Engine 仍在启动；
- 5432 端口被电脑中另一个 PostgreSQL 占用；
- Docker 镜像下载失败。

检查 5432 端口：

```powershell
Get-NetTCPConnection -LocalPort 5432 -State Listen -ErrorAction SilentlyContinue
```

如果已有本机 PostgreSQL 占用 5432，应停止它，或者修改 Compose 端口和 backend `.env` 中的数据库端口。

### 18.2 后端提示数据库连接失败

依次检查：

```powershell
docker compose ps db
docker compose exec db pg_isready -U postgres -d mlagent
```

再检查 `backend/.env`：

```dotenv
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/mlagent
```

Windows 本地后端必须使用 `localhost`，不能使用 Docker 内部服务名 `db`。

### 18.3 后端提示缺少 Python 模块

例如：

```text
ModuleNotFoundError: No module named 'sqlmodel'
```

说明当前 PowerShell 没有使用正确虚拟环境，或者依赖没有安装完成。

执行：

```powershell
cd C:\projects\MLAgent\backend
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

确认提示符前有 `(.venv)`，然后重新启动后端。

### 18.4 PowerShell 不允许激活虚拟环境

执行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

不要为了这个问题直接把整台电脑的执行策略永久设置为 Unrestricted。

### 18.5 前端安装出现 ERESOLVE

典型内容：

```text
ERESOLVE could not resolve
react-scripts@5.0.1
typescript
```

使用项目要求的命令：

```powershell
npm ci --legacy-peer-deps
```

不要省略 `--legacy-peer-deps`。

### 18.6 3000 或 8000 端口被占用

检查：

```powershell
Get-NetTCPConnection -LocalPort 3000,8000 -State Listen -ErrorAction SilentlyContinue
```

通常是之前启动的前端或后端仍在运行。找到原来的 PowerShell 并按 `Ctrl+C`，不要重复启动多个实例。

如果前端端口改为其他值，还需要同步修改 backend `.env` 中的 `CORS_ORIGINS`。新手建议先释放原端口，而不是修改端口。

### 18.7 前端页面打不开

检查运行 `npm start` 的 PowerShell：

- 是否显示 `Compiled successfully!`；
- 是否出现红色编译错误；
- 窗口是否已经被关闭；
- 地址是否为 <http://localhost:3000>。

如果依赖损坏，可以重新执行：

```powershell
cd C:\projects\MLAgent\frontend
npm ci --legacy-peer-deps
npm start
```

### 18.8 前端提示无法连接后端

先访问：

<http://localhost:8000/health>

如果打不开，检查后端 PowerShell 是否仍在运行。前端默认把 API 请求发送到 `http://localhost:8000`。

还要检查 backend `.env`：

```dotenv
CORS_ORIGINS=["http://localhost:3000"]
```

修改 `.env` 后必须重启后端。

### 18.9 上传或生成产物时提示权限错误

检查：

```powershell
Get-ChildItem C:\app
```

确认 `C:\app\uploads` 和 `C:\app\artifacts` 存在，并且当前 Windows 用户可以创建文件。

可以测试：

```powershell
New-Item -ItemType File -Path C:\app\write-test.txt -Force
Remove-Item C:\app\write-test.txt
```

如果提示拒绝访问，请参考第 9 节配置目录权限。

### 18.10 模型接口失败

| 状态 | 排查方向 |
| --- | --- |
| 401 | API Key 是否正确、是否过期 |
| 403 | 是否拥有该模型权限 |
| 404 | 模型名称和 Base URL 是否正确 |
| 429 | 额度和频率限制 |
| timeout | 网络、代理、服务商状态或模型响应时间 |

同时查看运行后端的 PowerShell，后端会输出更详细的请求错误。

### 18.11 训练长时间没有完成

可能原因：

- 数据量较大；
- 特征数量较多；
- HPO trial 数量较多；
- 电脑 CPU 或内存不足；
- LLM 请求仍在等待；
- 某个模型训练较慢。

先查看后端 PowerShell 是否仍有新日志。只要进程仍在运行且没有 Traceback，不要连续重复点击训练按钮。

## 19. 数据、密钥和安全注意事项

### 19.1 不能上传到 GitHub 的内容

- `backend/.env`；
- 真实 LLM API Key；
- 生产数据库密码；
- SSH 私钥；
- 含敏感信息的数据集；
- `C:\app` 中的真实业务数据和训练产物。

`.env.example` 可以上传，因为它只提供配置格式，不应包含真实密钥。

### 19.2 备份重要数据

数据库数据位于 Docker volume，上传文件和运行产物位于 `C:\app`。

需要保留完整实验时，应同时备份：

- PostgreSQL 数据库；
- `C:\app\uploads`；
- `C:\app\artifacts`；
- 下载的 Final Output ZIP。

只复制 GitHub 代码不能恢复历史任务和训练结果。

### 19.3 清空开发数据库

只有明确需要删除所有历史任务时，才可以在项目根目录执行：

```powershell
docker compose down -v
docker compose up -d db
```

> 警告：`docker compose down -v` 会永久删除当前项目的 PostgreSQL volume。执行前必须确认数据库内容不再需要。

该命令不会自动删除 `C:\app` 中的文件。如需清理产物，应先人工检查并备份，不能在不确认内容的情况下删除整个目录。

## 20. 项目目录说明

```text
MLAgent/
├─ backend/                  Windows 本地 FastAPI 后端
│  ├─ .venv/                 本地 Python 虚拟环境，不上传 GitHub
│  ├─ .env                   本地后端配置，不上传 GitHub
│  ├─ app/                   后端源码
│  ├─ alembic/               数据库迁移文件
│  ├─ tests/                 后端测试
│  └─ requirements.txt       Python 依赖列表
├─ frontend/                 Windows 本地 React 前端
│  ├─ node_modules/          npm 安装的依赖，不上传 GitHub
│  ├─ src/                   前端源码
│  ├─ public/                前端公共资源
│  ├─ package.json           前端依赖和命令
│  └─ package-lock.json      锁定依赖版本
├─ docker-compose.yml        本地开发 Compose 配置，本方案只启动 db
├─ docker-compose.prod.yml   生产容器配置，本地方案不使用
└─ readme本地.md             本文档

C:\app/
├─ uploads/                  上传的数据集
└─ artifacts/                特征、模型、评估和最终输出产物
```

## 21. 最终检查清单

### 安装检查

- [ ] `git --version` 能显示版本；
- [ ] `py -3.12 --version` 能显示 Python 3.12；
- [ ] `node --version` 和 `npm --version` 能显示版本；
- [ ] Docker Desktop 已启动；
- [ ] `docker info` 能显示 Server 信息。

### 数据库检查

- [ ] 只执行了 `docker compose up -d db`；
- [ ] `docker compose ps db` 显示 healthy；
- [ ] `pg_isready` 显示 accepting connections；
- [ ] 没有启动 Docker 版 frontend 和 backend。

### 后端检查

- [ ] backend 中已创建 `.venv`；
- [ ] 激活环境后提示符前有 `(.venv)`；
- [ ] `requirements.txt` 安装完成；
- [ ] backend 中已创建 `.env`；
- [ ] DATABASE_URL 使用 `localhost:5432`；
- [ ] `C:\app\uploads` 和 `C:\app\artifacts` 存在且可写；
- [ ] uvicorn 正在 Windows 本机运行；
- [ ] <http://localhost:8000/health> 返回 `{"status":"ok"}`。

### 前端检查

- [ ] 已执行 `npm ci --legacy-peer-deps`；
- [ ] frontend 中存在 `node_modules`；
- [ ] `npm start` 显示 `Compiled successfully!`；
- [ ] <http://localhost:3000> 能正常打开。

### 使用检查

- [ ] 已通过 **Switch Model** 验证模型配置；
- [ ] 能提交 Task Specification；
- [ ] 能看到左侧工作流菜单；
- [ ] 能上传数据并运行 Dataset Profile；
- [ ] 知道按第 15.2 节从上到下运行工作流；
- [ ] 知道如何查看历史任务；
- [ ] 知道如何按 `Ctrl+C` 停止本地前端和后端；
- [ ] 知道 `docker compose down -v` 会永久删除数据库数据。

如果某项未完成，请停在对应步骤查看第 18 节，不要在原因不明时删除 `.venv`、`node_modules`、Docker volume 或 `C:\app` 中的数据。
