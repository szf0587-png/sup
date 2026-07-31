# 快速测试指南

## 当前完成状态

✅ **任务 #8：数据库层** - 已完成
✅ **任务 #9：认证系统** - 已完成
✅ **数据库初始化** - 已完成
✅ **集成到 FastAPI** - 已完成

## 快速测试步骤

### 1. 测试认证系统集成
```bash
cd "D:\Work space\GEO\supermap\src\tianyan-cangqiong"
python scripts/test_auth_integration.py
```

### 2. 启动服务器
```bash
python server/main.py
```

启动后访问：http://localhost:8000/docs

### 3. 测试登录功能

在 Swagger UI 中：
1. 找到 `POST /api/auth/login`
2. 点击 "Try it out"
3. 输入：
   ```json
   {
     "username": "admin",
     "password": "admin123"
   }
   ```
4. 点击 "Execute"
5. 如果看到 `access_token`，说明登录成功！

### 4. 测试获取用户信息

1. 复制上一步返回的 `access_token`
2. 点击页面右上角的 "Authorize" 按钮
3. 输入：`Bearer <your-token>`
4. 点击 "Authorize"
5. 找到 `GET /api/auth/me`
6. 点击 "Try it out" -> "Execute"
7. 应该看到管理员的用户信息

### 5. 测试注册新用户

1. 找到 `POST /api/auth/register`
2. 点击 "Try it out"
3. 输入：
   ```json
   {
     "username": "testuser",
     "email": "test@example.com",
     "password": "password123",
     "display_name": "测试用户"
   }
   ```
4. 点击 "Execute"
5. 如果返回新用户信息，说明注册成功！

## 验证要点

✅ 服务器能正常启动
✅ `/docs` 页面能访问
✅ 能看到 6 个认证相关的 API 端点
✅ 管理员账号能登录成功
✅ 能获取当前用户信息
✅ 能注册新用户

## 如果遇到问题

### 问题：启动失败
- 检查数据库是否初始化：`ls database/tianyan.db`
- 重新初始化：`python scripts/init_database.py`

### 问题：导入错误
- 检查依赖是否安装：`python scripts/check_dependencies.py`
- 重新安装：`pip install sqlalchemy bcrypt pyjwt`

### 问题：登录失败
- 确认用户名和密码：`admin` / `admin123`
- 检查数据库中是否有管理员账号

## 下一步

测试通过后，可以开始：
- **任务 #10：数据上传管理**
- **任务 #11：项目管理**
- **任务 #12：重构现有 API**
