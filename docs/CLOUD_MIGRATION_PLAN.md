# 云端迁移方案 - 从本地到服务器的平滑过渡

## 设计原则

✅ **抽象分离**：存储层、认证层、计算层独立抽象  
✅ **配置驱动**：通过配置文件切换本地/云端模式  
✅ **渐进迁移**：先迁移认证和数据库，后迁移文件和计算  
✅ **向后兼容**：云端版本可降级到本地模式

---

## 一、架构抽象层设计

### 1. 存储抽象层（Storage Adapter）

```python
# server/storage/__init__.py
from abc import ABC, abstractmethod
from pathlib import Path

class StorageBackend(ABC):
    """存储后端抽象接口"""
    
    @abstractmethod
    def save_file(self, file_data: bytes, relative_path: str) -> str:
        """保存文件，返回访问路径"""
        pass
    
    @abstractmethod
    def get_file(self, relative_path: str) -> bytes:
        """读取文件"""
        pass
    
    @abstractmethod
    def delete_file(self, relative_path: str) -> bool:
        """删除文件"""
        pass
    
    @abstractmethod
    def list_files(self, prefix: str) -> list[str]:
        """列出文件"""
        pass
    
    @abstractmethod
    def get_public_url(self, relative_path: str) -> str:
        """获取文件的公开访问 URL"""
        pass


# server/storage/local.py
class LocalStorageBackend(StorageBackend):
    """本地文件系统存储"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def save_file(self, file_data: bytes, relative_path: str) -> str:
        file_path = self.base_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(file_data)
        return str(relative_path)
    
    def get_file(self, relative_path: str) -> bytes:
        file_path = self.base_dir / relative_path
        return file_path.read_bytes()
    
    def delete_file(self, relative_path: str) -> bool:
        file_path = self.base_dir / relative_path
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    def list_files(self, prefix: str) -> list[str]:
        prefix_path = self.base_dir / prefix
        if not prefix_path.exists():
            return []
        return [str(p.relative_to(self.base_dir)) for p in prefix_path.rglob("*") if p.is_file()]
    
    def get_public_url(self, relative_path: str) -> str:
        # 本地模式：返回相对路径（通过 /api/files/download/{path} 访问）
        return f"/api/files/download/{relative_path}"


# server/storage/s3.py
import boto3

class S3StorageBackend(StorageBackend):
    """云端 S3 对象存储（阿里云 OSS / 腾讯云 COS / AWS S3）"""
    
    def __init__(self, bucket: str, endpoint: str, access_key: str, secret_key: str):
        self.bucket = bucket
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
    
    def save_file(self, file_data: bytes, relative_path: str) -> str:
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=relative_path,
            Body=file_data
        )
        return relative_path
    
    def get_file(self, relative_path: str) -> bytes:
        response = self.s3_client.get_object(Bucket=self.bucket, Key=relative_path)
        return response['Body'].read()
    
    def delete_file(self, relative_path: str) -> bool:
        self.s3_client.delete_object(Bucket=self.bucket, Key=relative_path)
        return True
    
    def list_files(self, prefix: str) -> list[str]:
        response = self.s3_client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
        return [obj['Key'] for obj in response.get('Contents', [])]
    
    def get_public_url(self, relative_path: str) -> str:
        # 云端模式：返回 CDN URL 或预签名 URL
        return self.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': relative_path},
            ExpiresIn=3600
        )


# server/storage/factory.py
from server.config import STORAGE_TYPE, DATA_DIR, S3_CONFIG

def get_storage_backend() -> StorageBackend:
    """根据配置返回存储后端"""
    if STORAGE_TYPE == "local":
        return LocalStorageBackend(DATA_DIR)
    elif STORAGE_TYPE == "s3":
        return S3StorageBackend(**S3_CONFIG)
    else:
        raise ValueError(f"Unknown storage type: {STORAGE_TYPE}")

# 全局单例
storage = get_storage_backend()
```

---

### 2. 数据库抽象层（Database Adapter）

```python
# server/config.py
import os

# 数据库配置（通过环境变量切换）
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite")  # sqlite / postgresql

if DATABASE_TYPE == "sqlite":
    DATABASE_URL = "sqlite:///./database/tianyan.db"
elif DATABASE_TYPE == "postgresql":
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/tianyan"
    )
else:
    raise ValueError(f"Unsupported database: {DATABASE_TYPE}")


# server/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from server.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    pool_pre_ping=True,  # 云端数据库连接健康检查
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_db():
    """数据库会话依赖注入"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

### 3. iServer 抽象层（GIS Compute Adapter）

```python
# server/gis/__init__.py
from abc import ABC, abstractmethod

class GISComputeBackend(ABC):
    """GIS 计算后端抽象"""
    
    @abstractmethod
    def spatial_buffer(self, geometry: dict, distance: float) -> dict:
        pass
    
    @abstractmethod
    def overlay_analysis(self, geom1: dict, geom2: dict, mode: str) -> dict:
        pass
    
    @abstractmethod
    def publish_dataset(self, file_path: str, service_name: str) -> dict:
        pass


# server/gis/iserver_local.py
class iServerLocalBackend(GISComputeBackend):
    """本地 iServer 实例"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url  # http://127.0.0.1:8090
    
    def spatial_buffer(self, geometry: dict, distance: float) -> dict:
        from server.integrations import iserver_client
        return iserver_client.spatial_buffer(geometry, distance)
    
    # ... 其他方法


# server/gis/iserver_cloud.py
class iServerCloudBackend(GISComputeBackend):
    """云端 iServer 实例（公网访问）"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url  # https://gis.example.com/iserver
        self.api_key = api_key
    
    def spatial_buffer(self, geometry: dict, distance: float) -> dict:
        # 调用云端 iServer，带 API Key 认证
        import requests
        response = requests.post(
            f"{self.base_url}/spatialanalyst/geometry/buffer.json",
            json={"geometry": geometry, "distance": distance},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()
    
    def publish_dataset(self, file_path: str, service_name: str) -> dict:
        # 云端模式：先上传文件到云存储，再通知 iServer 发布
        from server.storage import storage
        
        # 1. 上传文件到 S3
        with open(file_path, 'rb') as f:
            s3_path = storage.save_file(f.read(), f"datasets/{service_name}.udbx")
        
        # 2. 调用云端 iServer Manager API
        s3_url = storage.get_public_url(s3_path)
        response = requests.post(
            f"{self.base_url}/manager/services.json",
            json={
                "datasource_url": s3_url,
                "service_name": service_name
            },
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()


# server/gis/factory.py
from server.config import GIS_BACKEND, ISERVER_BASE, ISERVER_API_KEY

def get_gis_backend() -> GISComputeBackend:
    if GIS_BACKEND == "local":
        return iServerLocalBackend(ISERVER_BASE)
    elif GIS_BACKEND == "cloud":
        return iServerCloudBackend(ISERVER_BASE, ISERVER_API_KEY)
    else:
        raise ValueError(f"Unknown GIS backend: {GIS_BACKEND}")

gis = get_gis_backend()
```

---

## 二、配置文件结构（环境变量 + .env）

```bash
# .env.local（本地开发）
DEPLOYMENT_MODE=local
DATABASE_TYPE=sqlite
STORAGE_TYPE=local
GIS_BACKEND=local

ISERVER_BASE=http://127.0.0.1:8090
ISERVER_USER=admin
ISERVER_PASSWORD=

FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000


# .env.cloud（云端生产）
DEPLOYMENT_MODE=cloud
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:pass@db.example.com:5432/tianyan
STORAGE_TYPE=s3
GIS_BACKEND=cloud

# S3 对象存储配置（阿里云 OSS）
S3_ENDPOINT=https://oss-cn-beijing.aliyuncs.com
S3_BUCKET=tianyan-data
S3_ACCESS_KEY=LTAI5t...
S3_SECRET_KEY=xxx...

# 云端 iServer 配置
ISERVER_BASE=https://gis.example.com/iserver
ISERVER_API_KEY=sk_prod_xxx...

# 认证配置
SECRET_KEY=production-secret-key-change-me
ACCESS_TOKEN_EXPIRE_HOURS=8

# Redis（云端会话管理，可选）
REDIS_URL=redis://cache.example.com:6379/0

FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
```

---

## 三、业务代码调用示例（与模式无关）

```python
# server/api/datasets.py
from fastapi import APIRouter, UploadFile, Depends
from server.storage import storage  # 自动根据配置选择后端
from server.middleware.auth_middleware import get_current_user

router = APIRouter()

@router.post("/datasets/upload/vector")
async def upload_vector(
    file: UploadFile,
    name: str,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    
    # 1. 读取文件
    file_data = await file.read()
    
    # 2. 保存到存储后端（本地文件系统 或 S3）
    relative_path = f"users/{user_id}/vector/{file.filename}"
    storage.save_file(file_data, relative_path)
    
    # 3. 获取访问 URL（本地路径 或 CDN URL）
    file_url = storage.get_public_url(relative_path)
    
    # 4. 保存元数据到数据库
    from server.models.dataset import Dataset
    from server.database import get_db
    
    db = next(get_db())
    dataset = Dataset(
        user_id=user_id,
        name=name,
        type="vector",
        file_path=relative_path,
        file_url=file_url
    )
    db.add(dataset)
    db.commit()
    
    return {"dataset_id": dataset.id, "file_url": file_url}


# server/api/screening.py
from server.gis import gis  # 自动根据配置选择后端

@router.post("/analysis/spatial-buffer")
async def spatial_buffer_analysis(
    geometry: dict,
    distance: float,
    current_user: dict = Depends(get_current_user)
):
    # 调用 GIS 后端（本地 iServer 或 云端 iServer）
    result = gis.spatial_buffer(geometry, distance)
    return result
```

**关键点**：业务代码完全不关心底层是本地还是云端，通过依赖注入自动适配。

---

## 四、迁移步骤（分阶段实施）

### Phase 1: 本地多用户（当前目标）
- ✅ SQLite 数据库
- ✅ 本地文件系统
- ✅ 本地 iServer 实例
- ✅ JWT 认证
- **时间**：2 周

### Phase 2: 云端数据库迁移
- 🔄 切换到 PostgreSQL（阿里云 RDS / 腾讯云数据库）
- 🔄 导出本地 SQLite 数据
- 🔄 导入到云端数据库
- **操作**：修改 `.env` 中的 `DATABASE_TYPE=postgresql`
- **时间**：1 天

### Phase 3: 云端文件存储迁移
- 🔄 开通对象存储（阿里云 OSS / 腾讯云 COS）
- 🔄 上传本地 `data/users/` 到 OSS
- 🔄 修改配置 `STORAGE_TYPE=s3`
- **时间**：1 天

### Phase 4: 云端 iServer 部署
- 🔄 在云服务器上安装 SuperMap iServer
- 🔄 配置公网访问（需要域名 + SSL 证书）
- 🔄 修改配置 `GIS_BACKEND=cloud`
- **时间**：3-5 天（含服务器配置）

### Phase 5: 生产优化
- 🔄 Redis 缓存（会话管理、GEE 缓存）
- 🔄 Nginx 反向代理
- 🔄 Docker 容器化部署
- 🔄 自动备份脚本
- **时间**：1 周

---

## 五、云端部署架构图

```
┌─────────────────────────────────────────────────────────┐
│                      用户浏览器                          │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Nginx 反向代理 + SSL 证书                   │
│           (gis.example.com / www.tianyan.com)           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          FastAPI 应用（多实例 + 负载均衡）               │
│         ├── 认证中间件（JWT）                            │
│         ├── 业务 API（不变）                             │
│         └── 存储抽象层 / GIS 抽象层                      │
└──┬──────────────┬────────────────┬────────────────┬─────┘
   │              │                │                │
   ▼              ▼                ▼                ▼
┌─────────┐  ┌─────────┐  ┌─────────────┐  ┌─────────────┐
│PostgreSQL│  │ Redis   │  │ 阿里云 OSS  │  │云端 iServer │
│ (RDS)   │  │ (缓存)  │  │ (文件存储)  │  │(GIS 计算)   │
└─────────┘  └─────────┘  └─────────────┘  └─────────────┘
```

---

## 六、云服务选型建议（国内）

### 1. 云服务器（ECS）
| 服务商 | 配置 | 价格 | 备注 |
|--------|------|------|------|
| 阿里云 | 2核4G + 5M带宽 | ~300 元/月 | 学生优惠 ~10 元/月 |
| 腾讯云 | 2核4G + 5M带宽 | ~280 元/月 | 新用户首年优惠 |
| 华为云 | 2核4G + 5M带宽 | ~320 元/月 | 国企首选 |

**推荐**：阿里云（文档完善，生态丰富）

### 2. 数据库（RDS PostgreSQL）
| 服务商 | 配置 | 价格 | 备注 |
|--------|------|------|------|
| 阿里云 RDS | 1核2G + 20GB | ~200 元/月 | 包含自动备份 |
| 腾讯云数据库 | 1核2G + 20GB | ~180 元/月 | 按量计费可选 |

**替代方案**：自建 PostgreSQL（安装在 ECS 上，省钱但需要手动维护）

### 3. 对象存储（OSS）
| 服务商 | 价格 | 备注 |
|--------|------|------|
| 阿里云 OSS | ~0.12 元/GB/月 + 流量费 | 40GB 资源包 ~9 元/年 |
| 腾讯云 COS | ~0.118 元/GB/月 | 50GB 免费额度 |

**成本估算**：100GB 数据 + 10GB 月流量 ≈ 20 元/月

### 4. CDN（加速文件访问）
| 服务商 | 价格 | 备注 |
|--------|------|------|
| 阿里云 CDN | ~0.2 元/GB 流量 | 新用户有免费流量包 |

---

## 七、成本估算

### 本地部署（当前方案）
- **硬件**：一台开机的电脑（已有）
- **软件**：全部免费
- **总成本**：0 元/月

### 云端最小化部署
- 云服务器：300 元/月
- 数据库：200 元/月（或自建省 200）
- 对象存储：20 元/月
- 域名：50 元/年
- SSL 证书：免费（Let's Encrypt）
- **总成本**：~520 元/月（或 320 元/月 自建数据库）

### 云端生产级部署
- 云服务器（多实例）：1000 元/月
- 数据库（主从）：800 元/月
- 对象存储 + CDN：100 元/月
- Redis 缓存：150 元/月
- 负载均衡：100 元/月
- 短信服务：按量计费
- **总成本**：~2150 元/月

---

## 八、代码改造清单

### 需要改造的文件

```bash
# 新增文件
server/storage/__init__.py         # 存储抽象层
server/storage/local.py            # 本地存储实现
server/storage/s3.py               # S3 存储实现
server/storage/factory.py          # 存储工厂

server/gis/__init__.py             # GIS 抽象层
server/gis/iserver_local.py        # 本地 iServer
server/gis/iserver_cloud.py        # 云端 iServer
server/gis/factory.py              # GIS 工厂

# 需要修改的文件
server/config.py                   # 添加模式配置
server/database.py                 # 支持 PostgreSQL
server/api/datasets.py             # 使用 storage 抽象
server/api/screening.py            # 使用 gis 抽象
server/integrations/gee_client.py  # 缓存路径使用 storage
server/services/spatial_analysis.py # 使用 gis 抽象

# 配置文件
.env.local                         # 本地配置
.env.cloud                         # 云端配置
.gitignore                         # 忽略 .env 文件
```

### 代码改造量估算
- 新增代码：~800 行
- 修改代码：~200 行
- 测试工作：2-3 天

---

## 九、迁移检查清单

### 迁移前（本地测试）
- [ ] 本地多用户功能完整测试
- [ ] 数据库备份脚本就绪
- [ ] 用户数据导出工具就绪
- [ ] 云服务账号开通完成
- [ ] 域名备案完成（国内必需）

### 迁移中（逐步切换）
- [ ] 数据库迁移（SQLite → PostgreSQL）
- [ ] 数据导入验证（用户数、数据集数）
- [ ] 文件上传测试（OSS 写入）
- [ ] iServer 云端部署与测试
- [ ] SSL 证书配置
- [ ] Nginx 配置与测试

### 迁移后（生产验证）
- [ ] 功能回归测试（所有 API）
- [ ] 性能测试（并发 50 用户）
- [ ] 备份恢复演练
- [ ] 监控告警配置
- [ ] 用户文档更新

---

## 十、回滚策略

如果云端部署失败，可以立即回滚到本地模式：

```bash
# 1. 修改配置
cp .env.local .env

# 2. 导出云端数据库
pg_dump tianyan > backup.sql

# 3. 导入到本地 SQLite
# 使用 pgloader 或手动迁移

# 4. 下载 OSS 文件到本地
aws s3 sync s3://tianyan-data/users/ data/users/

# 5. 重启服务
python server/main.py
```

---

## 总结

通过抽象层设计，系统可以在**本地模式**和**云端模式**之间无缝切换：

| 模式 | 数据库 | 文件存储 | GIS 计算 | 适用场景 |
|------|--------|----------|----------|----------|
| **本地** | SQLite | 文件系统 | 本地 iServer | 个人/团队内网使用 |
| **云端** | PostgreSQL | 对象存储 | 云端 iServer | 公网访问/多人协作 |

**核心优势**：
1. ✅ 现在立即开发本地版本，零云成本
2. ✅ 未来随时迁移云端，只需改配置
3. ✅ 业务代码无需改动，抽象层自动适配
4. ✅ 支持混合模式（数据库上云，文件本地）

**实施建议**：先完成本地版本（2周），稳定运行 1-2 个月后，再考虑云端迁移。
