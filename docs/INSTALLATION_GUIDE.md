# 任务 #8 和 #9 完成后的安装与初始化指南

## 📦 步骤 1：安装依赖包

在 `terroir_hunter` 环境中执行以下命令：

```bash
# 激活 conda 环境（如果尚未激活）
conda activate terroir_hunter

# 进入项目目录
cd "D:\Work space\GEO\supermap\src\tianyan-cangqiong"

# 安装数据库和认证相关依赖
pip install sqlalchemy bcrypt pyjwt
```

## ✅ 步骤 2：检查依赖是否安装成功

```bash
python scripts/check_dependencies.py
```

**预期输出：**
```
=== 检查多用户系统依赖包 ===

✓ sqlalchemy      - 数据库 ORM
✓ bcrypt          - 密码加密
✓ jwt             - JWT 令牌（安装包名: pyjwt）

所有依赖包已安装，可以运行数据库初始化脚本

运行: python scripts/init_database.py
```

## 🗄️ 步骤 3：初始化数据库

```bash
python scripts/init_database.py
```

**预期输出：**
```
=== 数据库模型导入测试 ===

1. 导入 Base 和 engine...
   ✓ 数据库连接配置导入成功

2. 导入 User 模型...
   ✓ User 表名: users

3. 导入 Dataset 模型...
   ✓ Dataset 表名: datasets

4. 导入 Project 模型...
   ✓ Project 表名: projects

5. 导入 AnalysisTask 模型...
   ✓ AnalysisTask 表名: analysis_tasks

6. 导入 GEECredential 模型...
   ✓ GEECredential 表名: gee_credentials

7. 导入 IServerService 模型...
   ✓ IServerService 表名: iserver_services

8. 导入密码工具...
   ✓ 密码工具导入成功

=== 所有模型导入成功 ===

9. 创建数据库表...
   ✓ 数据库表创建完成

10. 创建默认管理员账号...
   ✓ 管理员账号已创建: admin / admin123

=== 数据库初始化完成 ===
```

## 📁 验证数据库文件

初始化成功后，应该会生成数据库文件：

```bash
# 检查数据库文件是否存在
ls -lh database/tianyan.db
```

## 🧪 测试默认管理员账号

数据库初始化会创建一个默认管理员账号：

- **用户名**: `admin`
- **密码**: `admin123`
- **角色**: `admin`
- **邮箱**: `admin@local`

## 📋 已完成的功能模块

### 任务 #8：数据库层 ✅
- ✅ 数据库连接配置 (`server/database.py`)
- ✅ 6 个数据库模型：
  - `server/models/user.py` - 用户表
  - `server/models/dataset.py` - 数据集表
  - `server/models/project.py` - 项目表
  - `server/models/analysis_task.py` - 分析任务表
  - `server/models/gee_credential.py` - GEE 凭证表
  - `server/models/iserver_service.py` - iServer 服务表
- ✅ 密码工具 (`server/utils/password.py`)
- ✅ 初始化脚本 (`scripts/init_database.py`)

### 任务 #9：认证系统 ✅
- ✅ JWT 工具 (`server/utils/jwt_utils.py`)
- ✅ 认证中间件 (`server/middleware/auth.py`)
- ✅ 认证数据模型 (`server/schemas/auth.py`)
- ✅ 认证 API 路由 (`server/api/auth.py`)

**认证 API 端点：**
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/logout` - 用户登出
- `GET /api/auth/me` - 获取当前用户信息
- `PUT /api/auth/me` - 更新用户信息
- `POST /api/auth/change-password` - 修改密码

## 🔧 下一步：集成到 FastAPI 应用

初始化完成后，需要：

1. **更新 `server/app.py`**，添加认证路由：
   ```python
   from server.api.auth import router as auth_router
   
   app.include_router(auth_router)
   ```

2. **在启动时初始化数据库**：
   ```python
   from server.database import init_db
   
   @app.on_event("startup")
   async def startup_event():
       init_db()
   ```

3. **测试认证功能**：
   - 启动服务器
   - 访问 `http://localhost:8000/docs` 查看 API 文档
   - 测试注册、登录、获取用户信息等功能

## ⚠️ 重要提示

- **JWT 密钥**: 生产环境需要在 `.env` 中设置 `JWT_SECRET_KEY`
- **默认管理员**: 首次部署后应立即修改 `admin` 账号密码
- **数据库备份**: SQLite 数据库文件在 `database/tianyan.db`，定期备份

## 🐛 故障排查

### 问题：ImportError: No module named 'sqlalchemy'
**解决方案**：确保在 `terroir_hunter` 环境中安装了依赖包

### 问题：数据库初始化失败
**解决方案**：
1. 删除 `database/tianyan.db` 文件
2. 重新运行 `python scripts/init_database.py`

### 问题：管理员账号已存在
**说明**：这是正常的，数据库已经初始化过了，无需重复初始化
