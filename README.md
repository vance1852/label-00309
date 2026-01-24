# 服务器硬盘自动巡检平台

基于 Django + Vue 3 的服务器硬盘自动巡检系统，支持 SSH 远程连接、定时巡检、告警邮件通知等功能。

## How to Run

### 使用 Docker Compose 启动（推荐）

```bash
# 进入项目目录
cd label-00309

# 构建并启动所有服务
docker-compose up --build -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 手动启动

#### 1. 启动数据库

```bash
# Docker 启动 MySQL
docker run -d --name disk_inspection_mysql -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=root123456 \
  -e MYSQL_DATABASE=disk_inspection \
  -e MYSQL_USER=inspection \
  -e MYSQL_PASSWORD=inspection123 \
  mysql:8.0 --default-authentication-plugin=mysql_native_password \
  --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
```

#### 2. 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 数据库迁移
python manage.py makemigrations users servers inspections alerts schedules
python manage.py migrate

# 初始化数据
python manage.py init_data

# 启动服务
python manage.py runserver 0.0.0.0:8000
```

#### 3. 启动前端

```bash
cd frontend-admin

# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build
```

## Services

| 服务           | 端口                       | 说明                |
| -------------- | -------------------------- | ------------------- |
| frontend-admin | 8081 (Docker) / 5173 (Dev) | 管理后台前端        |
| backend        | 8000                       | Django API 服务     |
| mysql          | 3306                       | MySQL 数据库        |
| redis          | 6379                       | Redis 缓存/消息队列 |
| test-server    | 2222                       | SSH 测试服务器      |

## 测试账号

### 系统登录账号

| 用户名 | 密码     | 角色       |
| ------ | -------- | ---------- |
| admin  | admin123 | 超级管理员 |

### 测试服务器

系统已预配置一台测试服务器，用于测试 SSH 连接和巡检功能：

**Docker Compose 环境（自动启动）：**

| 配置项   | 值          |
| -------- | ----------- |
| 服务器名 | 测试服务器  |
| IP地址   | test-server |
| SSH端口  | 22          |
| 用户名   | root        |
| 密码     | root123     |

> Docker Compose 启动时会自动创建测试服务器容器，无需手动操作。

**本地开发环境（手动启动）：**

| 配置项   | 值         |
| -------- | ---------- |
| 服务器名 | 测试服务器 |
| IP地址   | 127.0.0.1  |
| SSH端口  | 2222       |
| 用户名   | root       |
| 密码     | root123    |

```bash
# 手动启动测试服务器 (本地开发时使用)
docker run -d --name test_server -p 2222:22 alpine:latest sh -c "apk add --no-cache openssh && ssh-keygen -A && echo 'root:root123' | chpasswd && sed -i 's/#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config && sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config && /usr/sbin/sshd -D"

# 查看状态
docker ps --filter name=test_server

# 停止并删除
docker rm -f test_server
```

#### 服务器功能测试步骤

1. 确保测试服务器 Docker 容器已启动
2. 登录系统后，进入"服务器管理"页面
3. 找到"测试服务器"，点击"测试"按钮验证 SSH 连接
4. 点击"巡检"按钮执行磁盘巡检
5. 进入"巡检记录"页面查看巡检结果

### 测试邮箱配置

系统已预配置以下邮箱用于告警测试：

| 配置项       | 值                   |
| ------------ | -------------------- |
| SMTP服务器   | smtp.163.com         |
| SMTP端口     | 465                  |
| 加密方式     | SSL                  |
| 邮箱账号     | z18203555732@163.com |
| 邮箱密码     | xy1028.              |
| 授权码       | WPptKqe2na7GtvsT     |
| 发件人邮箱   | z18203555732@163.com |
| 测试收件邮箱 | z18203555732@163.com |

> 注意：如需修改邮箱配置，请在"告警设置"页面更新 SMTP 密码（填写授权码）

### 邮件功能测试步骤

1. 登录系统后，进入"告警设置"页面
2. 点击"发送测试邮件"按钮
3. 在弹窗中输入收件邮箱：`z18203555732@163.com`
4. 点击"发送"按钮
5. 登录 163 邮箱 (z18203555732@163.com，密码：xy1028.) 查看是否收到测试邮件
6. 如未在收件箱找到，请检查垃圾邮件箱

## 题目内容

基于 Django 编写一个服务器硬盘自动巡检平台，需要实现的功能如下：

1. **服务器管理**：增加、修改、删除服务器，服务器信息涉及 IP、端口、账号、密码
2. **SSH 巡检**：使用 SSH 登录，输入配置好的命令后，将所有的返回结果保存在巡检历史记录中，对结果进行整理并发送告警邮件
3. **告警邮件设置**：设置告警邮件发送邮箱的设置，以及接收邮箱的设置
4. **巡检周期设置**：巡检周期可以设置
5. **用户认证**：有账号登录页面，需要登录后才能对平台内进行设置操作

## 功能特性

- ✅ 服务器 CRUD 管理
- ✅ SSH 连接测试
- ✅ 定时巡检任务
- ✅ 硬盘使用率监控
- ✅ 告警阈值设置
- ✅ 邮件告警通知
- ✅ 巡检历史记录
- ✅ JWT 用户认证
- ✅ 操作日志记录

## 技术栈

- **后端**: Django 4.2 + Django REST Framework + Celery + MySQL
- **前端**: Vue 3 + Vite + Element Plus + Pinia + Axios
- **部署**: Docker + Docker Compose + Nginx

## 项目结构

```
label-00309/
├── backend/                          # Django 后端
│   ├── apps/
│   │   ├── alerts/                   # 告警配置模块
│   │   │   ├── models.py             # 告警配置、收件人模型
│   │   │   ├── serializers.py        # 序列化器
│   │   │   ├── services.py           # 邮件发送服务
│   │   │   ├── views.py              # API 视图
│   │   │   └── urls.py               # 路由配置
│   │   ├── core/                     # 核心模块
│   │   │   ├── exceptions.py         # 全局异常处理
│   │   │   ├── middleware.py         # 请求日志中间件
│   │   │   ├── pagination.py         # 分页配置
│   │   │   └── response.py           # 统一响应格式
│   │   ├── inspections/              # 巡检模块
│   │   │   ├── models.py             # 巡检记录模型
│   │   │   ├── serializers.py        # 序列化器
│   │   │   ├── services.py           # SSH巡检服务
│   │   │   ├── views.py              # API 视图
│   │   │   └── urls.py               # 路由配置
│   │   ├── schedules/                # 调度模块
│   │   │   ├── models.py             # 调度配置模型
│   │   │   ├── tasks.py              # Celery 定时任务
│   │   │   ├── views.py              # API 视图
│   │   │   └── urls.py               # 路由配置
│   │   ├── servers/                  # 服务器管理模块
│   │   │   ├── models.py             # 服务器模型(密码加密)
│   │   │   ├── serializers.py        # 序列化器
│   │   │   ├── views.py              # API 视图
│   │   │   └── urls.py               # 路由配置
│   │   └── users/                    # 用户认证模块
│   │       ├── models.py             # 自定义用户模型
│   │       ├── serializers.py        # 序列化器
│   │       ├── views.py              # 登录/登出/修改密码
│   │       ├── urls.py               # 路由配置
│   │       └── management/commands/  # 管理命令
│   │           └── init_data.py      # 初始化数据
│   ├── config/                       # 项目配置
│   │   ├── settings.py               # Django 配置
│   │   ├── urls.py                   # 主路由
│   │   ├── celery.py                 # Celery 配置
│   │   └── wsgi.py                   # WSGI 入口
│   ├── scripts/
│   │   └── init.sql                  # 数据库初始化脚本
│   ├── Dockerfile                    # 后端 Docker 镜像
│   ├── entrypoint.sh                 # 容器启动脚本
│   ├── requirements.txt              # Python 依赖
│   └── manage.py                     # Django 管理脚本
├── frontend-admin/                   # Vue 3 管理后台
│   ├── src/
│   │   ├── api/                      # API 接口
│   │   │   ├── request.js            # Axios 封装
│   │   │   ├── auth.js               # 认证接口
│   │   │   ├── servers.js            # 服务器接口
│   │   │   ├── inspections.js        # 巡检接口
│   │   │   ├── alerts.js             # 告警接口
│   │   │   └── schedule.js           # 调度接口
│   │   ├── router/
│   │   │   └── index.js              # 路由配置
│   │   ├── stores/
│   │   │   └── user.js               # Pinia 用户状态
│   │   ├── styles/
│   │   │   └── index.scss            # 全局样式
│   │   ├── views/                    # 页面组件
│   │   │   ├── Login.vue             # 登录页
│   │   │   ├── Layout.vue            # 布局框架
│   │   │   ├── Dashboard.vue         # 仪表盘
│   │   │   ├── Servers.vue           # 服务器管理
│   │   │   ├── Inspections.vue       # 巡检记录
│   │   │   ├── Alerts.vue            # 告警设置
│   │   │   └── Schedule.vue          # 调度设置
│   │   ├── App.vue                   # 根组件
│   │   └── main.js                   # 入口文件
│   ├── public/
│   │   └── vite.svg                  # 网站图标
│   ├── Dockerfile                    # 前端 Docker 镜像
│   ├── nginx.conf                    # Nginx 配置
│   ├── package.json                  # NPM 依赖
│   ├── vite.config.js                # Vite 配置
│   └── index.html                    # HTML 模板
├── docs/
│   └── project_design.md             # 项目设计文档
├── docker-compose.yml                # Docker Compose 编排
├── .gitignore                        # Git 忽略文件
├── .prettierignore                   # Prettier 忽略文件
└── README.md                         # 项目说明
```
