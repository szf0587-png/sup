# 天眼寻珍·苍穹 - 本地多用户系统设计方案

## 设计目标

- ✅ 支持多用户注册/登录
- ✅ 用户数据完全隔离
- ✅ 本地 SQLite 数据库（无需额外服务器）
- ✅ 局域网内多人访问
- ✅ 共享本地 iServer 实例
- ✅ 每个用户绑定独立 GEE 账号

---

## 一、技术栈选型（本地优化）

### 1. 数据库：SQLite + SQLAlchemy
```python
# 优势
- 零配置，单文件数据库
- 支持完整 SQL 功能
- 事务支持
- 适合 < 100 用户并发

# 存储路径
D:\Work space\GEO\supermap\src\tianyan-cangqiong\
└── database/
    └── tianyan.db  # 所有用户数据
```

### 2. 认证：JWT Token + HTTPOnly Cookie
```python
# 优势
- 无状态认证（无需 Redis）
- 前端自动携带 Cookie
- XSS 防护（HTTPOnly）

# Token 有效期
- Access Token: 8 小时
- Refresh Token: 30 天（可选）
```

### 3. 文件存储：按用户 ID 分目录
```
data/
├── users/
│   ├── user_001/
│   │   ├── vector/          # 用户上传的矢量数据
│   │   ├── raster/          # 用户上传的栅格数据
│   │   ├── gee_cache/       # 用户的 GEE 缓存
│   │   ├── outputs/         # 报告输出
│   │   └── datasets.json    # 数据集元数据
│   └── user_002/
│       └── ...
└── shared/                  # 共享数据（可选）
    └── base_maps/
```

### 4. iServer：共享实例 + 用户前缀隔离
```python
# 本地 iServer 地址
ISERVER_BASE = "http://127.0.0.1:8090"

# 服务命名规则（避免冲突）
用户 A 发布的服务: data-userA_luonan_towns
用户 B 发布的服务: data-userB_luonan_towns

# 定期清理策略
- 7 天未使用的服务自动删除
- 用户删除时清理其所有服务
```

---

## 二、数据库设计

### 核心表结构

```sql
-- 用户表
CREATE TABLE users (
    id TEXT PRIMARY KEY,              -- UUID
    username TEXT UNIQUE NOT NULL,    -- 用户名
    email TEXT UNIQUE NOT NULL,       -- 邮箱
    password_hash TEXT NOT NULL,      -- bcrypt 加密
    display_name TEXT,                -- 显示名称
    role TEXT DEFAULT 'user',         -- 角色：admin / user
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- GEE 绑定表
CREATE TABLE gee_credentials (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    project_id TEXT NOT NULL,         -- GCP 项目 ID
    service_account_key TEXT,         -- 加密的服务账号 JSON
    refresh_token TEXT,               -- OAuth refresh token（加密）
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- 数据集表
CREATE TABLE datasets (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT NOT NULL,               -- 'vector' / 'raster'
    format TEXT,                      -- 'geojson' / 'tif' / 'shp'
    file_path TEXT NOT NULL,          -- 相对路径: users/{user_id}/vector/xxx.geojson
    size_bytes INTEGER,
    feature_count INTEGER,            -- 矢量要素数
    bounds_minx REAL,                 -- 空间范围
    bounds_miny REAL,
    bounds_maxx REAL,
    bounds_maxy REAL,
    crs TEXT DEFAULT 'EPSG:4326',
    metadata TEXT,                    -- JSON 字符串
    status TEXT DEFAULT 'active',     -- 'active' / 'processing' / 'error'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 项目表
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    region_name TEXT,                 -- 研究区名称
    bounds_minx REAL,
    bounds_miny REAL,
    bounds_maxx REAL,
    bounds_maxy REAL,
    dataset_towns TEXT,               -- 关联的乡镇数据集 ID
    dataset_dem TEXT,                 -- 关联的 DEM 数据集 ID
    dataset_constraints TEXT,         -- 关联的约束数据集 ID
    settings TEXT,                    -- JSON: {top_n: 5, weights: {...}}
    is_default BOOLEAN DEFAULT 0,     -- 是否为默认项目
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 分析任务表
CREATE TABLE analysis_tasks (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    task_type TEXT NOT NULL,          -- 'town_ranking' / 'parcel_eval' / 'spatial_buffer'
    status TEXT DEFAULT 'pending',    -- 'pending' / 'running' / 'completed' / 'error'
    input_params TEXT,                -- JSON 输入参数
    result TEXT,                      -- JSON 结果
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- iServer 服务注册表（跟踪用户发布的服务）
CREATE TABLE iserver_services (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    service_name TEXT UNIQUE NOT NULL,  -- 如 data-userA_luonan_towns
    dataset_id TEXT REFERENCES datasets(id) ON DELETE CASCADE,
    service_url TEXT,
    status TEXT DEFAULT 'active',       -- 'active' / 'deleted'
    last_accessed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_datasets_user ON datasets(user_id);
CREATE INDEX idx_projects_user ON projects(user_id);
CREATE INDEX idx_tasks_user ON analysis_tasks(user_id);
CREATE INDEX idx_services_user ON iserver_services(user_id);
```

---

## 三、目录结构调整

```
src/tianyan-cangqiong/
├── server/
│   ├── main.py                    # FastAPI 主入口
│   ├── config.py                  # 全局配置
│   ├── database.py                # ✨ 新增：数据库连接
│   ├── auth.py                    # ✨ 新增：JWT 工具函数
│   │
│   ├── models/                    # ✨ 新增：SQLAlchemy 模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── dataset.py
│   │   ├── project.py
│   │   ├── analysis_task.py
│   │   └── gee_credential.py
│   │
│   ├── api/
│   │   ├── auth.py                # ✨ 新增：注册/登录/登出
│   │   ├── users.py               # ✨ 新增：用户管理
│   │   ├── datasets.py            # ✨ 新增：数据上传/管理
│   │   ├── projects.py            # ✨ 新增：项目管理
│   │   ├── gee_binding.py         # ✨ 新增：GEE 绑定
│   │   ├── standards.py           # ✅ 已有
│   │   ├── phenology.py           # ✅ 已有
│   │   ├── screening.py           # ✅ 已有
│   │   └── parcels.py             # ✅ 已有
│   │
│   ├── services/
│   │   ├── auth_service.py        # ✨ 新增：认证业务逻辑
│   │   ├── dataset_service.py     # ✨ 新增：数据集业务逻辑
│   │   ├── project_service.py     # ✨ 新增：项目业务逻辑
│   │   ├── file_upload_service.py # ✨ 新增：文件上传处理
│   │   └── ...                    # 已有服务
│   │
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth_middleware.py     # ✨ 新增：JWT 认证中间件
│   │
│   └── utils/
│       ├── password.py            # ✨ 新增：密码加密
│       ├── file_utils.py          # ✨ 新增：文件处理工具
│       └── geo_utils.py           # ✨ 新增：GIS 工具函数
│
├── database/
│   ├── tianyan.db                 # ✨ SQLite 数据库
│   └── migrations/                # ✨ 数据库迁移脚本
│       └── init.sql
│
├── data/
│   ├── users/                     # ✨ 按用户隔离
│   │   └── {user_id}/
│   └── shared/                    # 共享资源（可选）
│
└── frontend/
    └── ...
```

---

## 四、核心 API 设计

### 1. 认证 API

```python
# POST /api/auth/register
{
  "username": "zhangsan",
  "email": "zhangsan@example.com",
  "password": "StrongPass123!",
  "display_name": "张三"
}
→ {"user_id": "user_001", "message": "注册成功"}

# POST /api/auth/login
{
  "username": "zhangsan",
  "password": "StrongPass123!"
}
→ {
    "access_token": "eyJ...",
    "user": {
      "id": "user_001",
      "username": "zhangsan",
      "display_name": "张三",
      "role": "user"
    }
  }
  # 同时设置 HTTPOnly Cookie: auth_token=eyJ...

# POST /api/auth/logout
→ {"message": "已登出"}
  # 清除 Cookie

# GET /api/auth/me
→ {"id": "user_001", "username": "zhangsan", ...}
```

### 2. 数据上传 API

```python
# POST /api/datasets/upload/vector
Content-Type: multipart/form-data
{
  "file": <GeoJSON/Shapefile>,
  "name": "洛南县乡镇边界",
  "tags": ["行政边界"]
}
→ {
    "dataset_id": "ds_abc123",
    "name": "洛南县乡镇边界",
    "type": "vector",
    "format": "geojson",
    "feature_count": 15,
    "bounds": [109.8, 33.8, 110.5, 34.4],
    "file_path": "users/user_001/vector/luonan_towns.geojson",
    "status": "active"
  }

# GET /api/datasets
→ {
    "datasets": [
      {"id": "ds_abc123", "name": "洛南县乡镇边界", ...},
      {"id": "ds_def456", "name": "洛南县 DEM", ...}
    ]
  }

# GET /api/datasets/{dataset_id}/preview
→ {
    "type": "FeatureCollection",
    "features": [...前 100 个要素]
  }

# DELETE /api/datasets/{dataset_id}
→ {"message": "数据集已删除"}
```

### 3. 项目管理 API

```python
# POST /api/projects
{
  "name": "洛南县农业评估",
  "region_name": "洛南县",
  "bounds": [109.8, 33.8, 110.5, 34.4],
  "dataset_towns": "ds_abc123",
  "dataset_dem": "ds_def456",
  "settings": {
    "top_n_towns": 5,
    "suitability_weight": 0.7,
    "phenology_weight": 0.3
  }
}
→ {"project_id": "proj_001", ...}

# GET /api/projects
→ {"projects": [{...}, {...}]}

# PUT /api/projects/{project_id}/activate
→ {"message": "项目已激活"}
  # 后续分析将基于此项目的配置和数据集
```

### 4. GEE 绑定 API

```python
# POST /api/integrations/gee/bind
{
  "project_id": "my-gcp-project",
  "service_account_key": "{...}"  # 或 OAuth 流程
}
→ {"message": "GEE 账号已绑定"}

# GET /api/integrations/gee/status
→ {
    "bound": true,
    "project_id": "my-gcp-project",
    "expires_at": "2026-08-26T10:00:00Z"
  }
```

---

## 五、认证流程实现

### JWT Token 生成与验证

```python
# server/auth.py
import jwt
from datetime import datetime, timedelta
from passlib.hash import bcrypt

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

def create_access_token(user_id: str, username: str) -> str:
    payload = {
        "sub": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def hash_password(password: str) -> str:
    return bcrypt.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.verify(plain, hashed)
```

### 认证中间件

```python
# server/middleware/auth_middleware.py
from fastapi import Request, HTTPException, status
from server.auth import verify_token

async def get_current_user(request: Request) -> dict:
    """从 Cookie 或 Authorization Header 获取当前用户"""
    token = request.cookies.get("auth_token")
    
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录"
        )
    
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已过期或无效"
        )
    
    return {"user_id": payload["sub"], "username": payload["username"]}
```

---

## 六、数据隔离实现

### 用户数据目录管理

```python
# server/utils/file_utils.py
from pathlib import Path
from server.config import DATA_DIR

def get_user_data_dir(user_id: str) -> Path:
    """获取用户数据根目录"""
    user_dir = DATA_DIR / "users" / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir

def get_user_vector_dir(user_id: str) -> Path:
    """获取用户矢量数据目录"""
    vector_dir = get_user_data_dir(user_id) / "vector"
    vector_dir.mkdir(exist_ok=True)
    return vector_dir

def get_user_raster_dir(user_id: str) -> Path:
    """获取用户栅格数据目录"""
    raster_dir = get_user_data_dir(user_id) / "raster"
    raster_dir.mkdir(exist_ok=True)
    return raster_dir

def get_user_gee_cache_dir(user_id: str) -> Path:
    """获取用户 GEE 缓存目录"""
    cache_dir = get_user_data_dir(user_id) / "gee_cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir
```

### iServer 服务命名隔离

```python
# server/integrations/iserver_client.py (改造)
def get_service_name(user_id: str, dataset_name: str) -> str:
    """生成唯一服务名（避免用户间冲突）"""
    # 去掉 user_ 前缀，使用前 8 位 UUID
    user_prefix = user_id.replace("user_", "")[:8]
    return f"{user_prefix}_{dataset_name}"

# 示例
user_id = "user_a1b2c3d4"
dataset_name = "luonan_towns"
service_name = get_service_name(user_id, dataset_name)
# → "a1b2c3d4_luonan_towns"
```

---

## 七、启动与部署

### 1. 初始化数据库

```bash
# 创建数据库和表
cd D:\Work space\GEO\supermap\src\tianyan-cangqiong
python -c "from server.database import init_db; init_db()"
```

### 2. 启动服务（局域网模式）

```bash
# 启动 iServer（所有用户共享）
E:\SuperMap\bin\startup.bat

# 启动 FastAPI（允许局域网访问）
cd src/tianyan-cangqiong/server
python main.py --host 0.0.0.0 --port 8000

# 局域网内其他电脑访问
http://192.168.1.100:8000
```

### 3. 创建第一个管理员账号

```bash
# 启动后自动创建 admin 账号
# 或通过注册 API 创建第一个用户
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@local",
    "password": "Admin123!",
    "display_name": "系统管理员"
  }'
```

---

## 八、前端改造要点

### 1. 登录页面（新增）

```javascript
// frontend/login.html
async function login() {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      username: document.getElementById('username').value,
      password: document.getElementById('password').value
    })
  });
  
  const data = await response.json();
  if (response.ok) {
    localStorage.setItem('user', JSON.stringify(data.user));
    window.location.href = '/index.html';
  } else {
    alert('登录失败: ' + data.detail);
  }
}
```

### 2. 数据上传页面（新增）

```javascript
// frontend/data-upload.html
async function uploadVector() {
  const formData = new FormData();
  formData.append('file', document.getElementById('fileInput').files[0]);
  formData.append('name', document.getElementById('datasetName').value);
  
  const response = await fetch('/api/datasets/upload/vector', {
    method: 'POST',
    body: formData
  });
  
  const data = await response.json();
  alert('上传成功！数据集 ID: ' + data.dataset_id);
}
```

### 3. 项目切换下拉菜单

```javascript
// 在主界面添加项目选择器
async function loadProjects() {
  const response = await fetch('/api/projects');
  const data = await response.json();
  
  const select = document.getElementById('projectSelector');
  data.projects.forEach(proj => {
    const option = document.createElement('option');
    option.value = proj.id;
    option.text = proj.name;
    select.appendChild(option);
  });
}

async function switchProject(projectId) {
  await fetch(`/api/projects/${projectId}/activate`, {method: 'PUT'});
  alert('已切换到项目: ' + projectId);
  location.reload();
}
```

---

## 九、与现有代码的兼容性

### 改造策略：最小侵入式

```python
# 1. 在需要用户上下文的 API 中注入依赖
from fastapi import Depends
from server.middleware.auth_middleware import get_current_user

@app.post("/api/analysis/town-ranking")
async def rank_towns(
    params: dict,
    current_user: dict = Depends(get_current_user)  # ✨ 注入用户信息
):
    user_id = current_user["user_id"]
    
    # 2. 使用用户的数据目录
    user_data_dir = get_user_data_dir(user_id)
    towns_file = user_data_dir / "vector" / "luonan_towns.geojson"
    
    # 3. 使用用户的项目配置
    project = get_active_project(user_id)
    towns_dataset_id = project.dataset_towns
    towns_file = get_dataset_file_path(towns_dataset_id)
    
    # 4. 调用原有业务逻辑（无需改动）
    result = town_ranking.rank_towns(...)
    return result
```

---

## 十、安全性考虑

### 1. 密码策略
- 最小长度 8 位
- 必须包含大小写字母 + 数字
- bcrypt 加密存储（成本因子 12）

### 2. 文件上传限制
- 单个文件 < 100 MB
- 允许的格式：`.geojson`, `.shp`, `.tif`, `.img`
- 病毒扫描（可选）

### 3. 数据访问控制
- 用户只能访问自己的数据
- 管理员可查看所有数据
- 项目共享功能（可选，Phase 2）

### 4. API 限流（可选）
- 每个用户每小时最多 1000 次请求
- GEE API 每天最多 100 次调用

---

## 十一、优势与限制

### ✅ 优势
1. **零外部依赖**：无需云服务器、域名、备案
2. **数据主权**：所有数据存储在本地，完全掌控
3. **成本低**：无需付费购买云资源
4. **快速部署**：5 分钟即可启动
5. **局域网共享**：办公室内多人协作

### ⚠️ 限制
1. **并发性能**：SQLite 写并发受限（适合 < 50 用户）
2. **可用性**：依赖本地电脑开机（可用树莓派 24 小时运行）
3. **外网访问**：需要内网穿透（frp / ngrok）
4. **备份责任**：需要手动备份数据库和文件

---

## 十二、实施步骤（建议 2 周完成）

### Week 1: 核心功能
- [ ] Day 1-2: 数据库设计与初始化
- [ ] Day 3-4: 用户注册/登录 API
- [ ] Day 5: 认证中间件与前端登录页
- [ ] Day 6-7: 数据上传 API 与文件管理

### Week 2: 集成与测试
- [ ] Day 8-9: 项目管理 API
- [ ] Day 10: GEE 绑定 API
- [ ] Day 11-12: 改造现有分析 API（注入用户上下文）
- [ ] Day 13-14: 前端集成测试与文档

---

## 附录：配置文件示例

```python
# server/config.py (修改)
DATABASE_URL = "sqlite:///./database/tianyan.db"
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
ACCESS_TOKEN_EXPIRE_HOURS = 8

# 文件上传限制
MAX_UPLOAD_SIZE_MB = 100
ALLOWED_VECTOR_FORMATS = [".geojson", ".shp", ".zip"]
ALLOWED_RASTER_FORMATS = [".tif", ".tiff", ".img"]

# iServer 共享配置（所有用户共用）
ISERVER_BASE = "http://127.0.0.1:8090"
ISERVER_USER = "admin"
ISERVER_PASSWORD = os.getenv("ISERVER_PASSWORD", "")

# 局域网访问
FASTAPI_HOST = "0.0.0.0"  # 允许局域网访问
FASTAPI_PORT = 8000
```

---

**总结**：这套方案完全适配本地部署，无需云服务器，通过 SQLite + 文件系统实现多用户隔离，共享本地 iServer 实例，每个用户绑定独立 GEE 账号。实施成本低，2 周即可完成基础版本。
