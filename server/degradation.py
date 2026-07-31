# 天眼寻珍·苍穹 — 离线降级配置

# GEE 离线模式
GEE_OFFLINE_MODE = True        # 默认使用缓存，不实时请求 GEE
GEE_CACHE_ENABLED = True       # 启用本地缓存
GEE_CACHE_TTL_DAYS = 365       # 缓存有效期

# AI 大棚检测
AI_REALTIME_ENABLED = False    # 默认关闭实时推理，使用预计算结果
AI_PRECOMPUTED_ENABLED = True  # 启用预计算结果兜底
AI_MODEL_PATH = None           # 模型路径（环境就绪后设置）

# 数据来源标记
DATA_SOURCE_LABELS = {
    "gee_realtime": "GEE 实时数据",
    "gee_cached": "GEE 本地缓存",
    "simulated": "模拟数据",
    "precomputed": "预计算结果",
    "ai_realtime": "AI 实时推理",
    "iserver_online": "iServer 在线",
    "iserver_offline": "iServer 离线（降级模式）",
}

# 功能开关（按计划书中条件设置）
FEATURE_FLAGS = {
    "image_service": False,     # PoC 未通过
    "three_d": False,           # 二维闭环未完成
    "ai_realtime": False,       # 默认预计算兜底
    "ai_precomputed": True,     # 预计算结果可用
    "gee_realtime": False,      # 默认缓存
    "gee_cache": True,          # 本地缓存可用
    "spatial_analysis": True,   # 降级为模拟
    "report_export": True,      # 固定模板可用
}

# 降级模式说明（展示在前端）
DEGRADATION_BANNER = {
    "gee_offline": "⚠️ GEE 不可用，使用本地缓存数据。数据时间范围: {date_range}",
    "ai_fallback": "⚠️ AI 实时推理不可用，使用预计算结果。结果验证状态: {verified}",
    "iserver_offline": "⚠️ iServer 不可用，空间分析使用模拟数据。",
    "simulated_data": "ℹ️ 当前使用模拟数据进行链路验证。真实 GIS 数据到位后将自动切换。",
    "image_service_disabled": "ℹ️ 影像服务未启用（PoC 阶段）。",
}
