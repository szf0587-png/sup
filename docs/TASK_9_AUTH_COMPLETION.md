# 任务 #9 认证系统完成指南

## ✅ 已完成的工作

### 任务 #8：数据库层
- ✅ 数据库连接配置 (`server/database.py`)
- ✅ 6 个数据库模型（User, Dataset, Project, AnalysisTask, GEECredential, IServerService）
- ✅ 密码加密工具 (`server/utils/password.py`)
- ✅ 数据库初始化成功，默认管理员账号已创建

### 任务 #9：认证系统
- ✅ JWT 令牌工具 (`server/utils/jwt_utils.py`)
- ✅ 认证中间件 (`server/middleware/auth.py`)
  - `get_current_user()` - 获取当前登录用户（必须登录）
  - `get_current_user_optional()` - 获取当前登录用户（可选）
  - `require_admin()` - 要求管理员权限
- ✅ 认证数据模型 (`server/schemas/auth.py`)
  - 6 个 Pydantic 模型用于请求/响应验证
- ✅ 认证 API 路由 (`server/api/auth.py`)
  - `POST /api/auth/register` - 用户注册
  - `POST /api/auth/login` - 用户登录（返回 JWT + 设置 Cookie）
  - `POST /api/auth/logout` - 用户登出
  - `GET /api/auth/me` - 获取当前用户信息
  - `PUT /api/auth/me` - 更新用户信息
  - `POST /api/auth/change-password` - 修改密码
- ✅ 集成到 FastAPI 主应用 (`server/main.py`)
  - 添加启动事件自动初始化数据库
  - 挂载认证路由

## 🧪 测试认证系统集成

运行集成测试脚本：

```bash
cd "D:\Work space\GEO\supermap\src\tianyan-cangqiong"
python scripts/test_auth_integration.py
```

**预期输出：**
```
=== 测试认证系统集成 ===

1. 导入 FastAPI 应用...
   ✓ 应用导入成功

2. 检查注册的路由...
   ✓ 认证相关路由数量: 6
     - POST                 /api/auth/register
     - POST                 /api/auth/login
     - POST                 /api/auth/logout
     - GET                  /api/auth/me
     - PUT                  /api/auth/me
     - POST                 /api/auth/change-password

3. 测试数据库连接...
   ✓ 数据库连接正常
   ✓ 管理员账号存在: admin (admin@local)

4. 测试认证中间件...
   ✓ 认证中间件导入成功

5. 测试 JWT 工具...
   ✓ 令牌生成成功: eyJ...
   ✓ 令牌验证成功: user_id=test_123

=== 所有测试通过 ===

🎉 认证系统已成功集成到 FastAPI 应用！
```

## 🚀 启动服务器

```bash
cd "D:\Work space\GEO\supermap\src\tianyan-cangqiong"
python server/main.py
```

服务器将在 `http://localhost:8000` 启动。

## 📖 测试 API 功能

### 1. 访问 API 文档

打开浏览器访问：http://localhost:8000/docs

可以看到 Swagger UI 自动生成的 API 文档，包括所有认证端点。

### 2. 使用管理员账号登录

**请求：**
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 28800
}
```

### 3. 获取当前用户信息

**请求（使用令牌）：**
```bash
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer <your-token>"
```

**响应：**
```json
{
  "id": "user_admin",
  "username": "admin",
  "email": "admin@local",
  "display_name": "系统管理员",
  "role": "admin",
  "is_active": true,
  "created_at": "2026-07-26T10:00:00",
  "last_login_at": "2026-07-26T10:05:00"
}
```

### 4. 注册新用户

**请求：**
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "zhangsan",
    "email": "zhangsan@example.com",
    "password": "password123",
    "display_name": "张三"
  }'
```

**响应：**
```json
{
  "id": "user_abc123456789",
  "username": "zhangsan",
  "email": "zhangsan@example.com",
  "display_name": "张三",
  "role": "user",
  "is_active": true,
  "created_at": "2026-07-26T10:10:00",
  "last_login_at": null
}
```

## 🔐 认证机制说明

### 双重令牌传递方式

系统支持两种方式传递 JWT 令牌：

1. **Authorization Header**（推荐用于 API 客户端）
   ```
   Authorization: Bearer <token>
   ```

2. **HTTPOnly Cookie**（推荐用于浏览器）
   - 登录成功后自动设置 `access_token` Cookie
   - 浏览器自动携带，无需手动管理
   - HTTPOnly 标志防止 XSS 攻击
   - SameSite=Lax 防止 CSRF 攻击

### 令牌有效期

- 默认有效期：**8 小时**
- 可通过环境变量 `ACCESS_TOKEN_EXPIRE_HOURS` 配置

### 受保护的路由示例

```python
from fastapi import Depends
from server.middleware.auth import get_current_user, require_admin
from server.models.user import User

# 需要登录
@app.get("/api/my-data")
def get_my_data(current_user: User = Depends(get_current_user)):
    return {"user_id": current_user.id, "data": [...]}

# 需要管理员权限
@app.delete("/api/users/{user_id}")
def delete_user(user_id: str, admin: User = Depends(require_admin)):
    # 只有管理员能访问
    pass

# 可选登录（未登录也能访问）
@app.get("/api/public-data")
def get_public_data(current_user: Optional[User] = Depends(get_current_user_optional)):
    if current_user:
        return {"message": f"欢迎，{current_user.username}"}
    else:
        return {"message": "欢迎访问（游客）"}
```

## 📋 下一步工作：任务 #10 数据上传管理

现在认证系统已完成，下一步是实现数据上传管理功能：

1. **文件上传 API**
   - 支持矢量数据（GeoJSON, Shapefile）
   - 支持栅格数据（GeoTIFF）
   - 自动创建用户数据目录：`data/users/{user_id}/vector|raster/`

2. **数据集 CRUD API**
   - 列出用户的所有数据集
   - 查看数据集详情（边界、CRS、元数据）
   - 删除数据集（软删除）
   - 数据集预览（缩略图）

3. **用户数据隔离**
   - 每个用户只能访问自己的数据集
   - 管理员可以查看所有数据集

4. **iServer 服务发布**
   - 上传数据后自动发布到 iServer
   - 服务命名：`{user_prefix}_{dataset_name}`
   - 记录到 `iserver_services` 表

## ⚠️ 安全注意事项

1. **JWT 密钥**
   - 生产环境必须设置强密钥：`export JWT_SECRET_KEY="your-secure-random-key"`
   - 可以使用 `openssl rand -hex 32` 生成随机密钥

2. **默认管理员密码**
   - 首次部署后立即修改 `admin` 账号密码
   - 使用 `POST /api/auth/change-password` 修改

3. **CORS 配置**
   - 当前配置允许 `localhost:8000` 访问
   - 生产环境需要更新 `allow_origins` 为实际域名

4. **HTTPS**
   - 生产环境必须使用 HTTPS
   - JWT 令牌通过 HTTPS 传输才安全

## 🎉 总结

**任务 #8 和 #9 已完成！**

- ✅ 数据库层（6 张表）
- ✅ 认证系统（JWT + 6 个 API 端点）
- ✅ 集成到 FastAPI 应用
- ✅ 数据库初始化成功
- ✅ 默认管理员账号可用

系统现在支持多用户注册、登录、身份验证。可以开始测试和使用认证功能了！
