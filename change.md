# 12345 市民热线系统 - 完整架构改进方案

> 生成日期：2025-01-15
> 版本：v1.0
> 状态：待实施

---

## 目录

- [一、现状问题总结](#一现状问题总结)
- [二、改进后的目录结构](#二改进后的目录结构)
- [三、各模块详细改进方案](#三各模块详细改进方案)
- [四、实施计划](#四实施计划)
- [五、风险评估与注意事项](#五风险评估与注意事项)

---

## 一、现状问题总结

经过对整个代码库的详细审查（共 47 个 Python 文件，约 4635 行代码），发现以下问题：

### 🔴 严重问题（P0 - 必须立即修复）

| 问题 | 位置 | 说明 | 风险等级 |
|------|------|------|----------|
| **API Key 硬编码** | `mcp_llm_clint.py:9` | `VLLM_KEY = "sk-5099122b..."` 直接写在代码中 | 🔴 高 |
| **Dify Key 默认值暴露** | `config/dify_config.py:13-24` | 虽然支持环境变量，但默认值是真实密钥 | 🔴 高 |
| **无异常分类** | `utils/exceptions.py` | 只有一个空的 `BusinessError` 类，仅 3 行代码 | 🟠 中 |

### 🟠 架构问题（P1 - 影响可维护性）

| 问题 | 说明 | 影响 |
|------|------|------|
| **日志系统简陋** | `utils/logger.py` 仅 15 行，无文件输出、无轮转、无请求追踪 | 难以排查问题 |
| **Service 层职责过重** | `daily_report_service.py` 有 788 行，混合了数据访问、业务逻辑、工具函数 | 难以测试和复用 |
| **大量重复的数据库连接管理** | 每个函数都要 `get_connection() / try / finally / release_connection()` | 代码冗余，易出错 |
| **三率计算重复实现** | `_calc_rates()` 在多个 service 文件中重复定义 | 维护困难 |
| **报告生成器高度相似但各自实现** | `dailyreport_llm_mcp.py`、`heatingreport_llm_mcp.py` 等结构几乎相同 | 代码重复 |

### 🟡 代码质量问题（P2 - 影响代码质量）

| 问题 | 说明 |
|------|------|
| **TypedDict 类型重复定义** | `heatingreport_types.py` 中 `OffSeasonStats` 定义了两次（第63行和第83行） |
| **缺少请求参数类型** | models 只定义了返回类型，没有 API 请求参数的类型定义 |
| **TypedDict 无运行时验证** | 无法自动验证数据格式、无默认值、无计算属性 |
| **配置分散** | 数据库配置在 `config.yaml`，Dify 在 `dify_config.py`，LLM 在 `mcp_llm_clint.py` |
| **MCP 端口硬编码** | 各个 MCP 服务器端口分散在不同文件中 |

### 🟢 运维问题（P3 - 影响运维效率）

| 问题 | 说明 |
|------|------|
| **需要手动启动 6 个服务** | 没有一键启动脚本 |
| **没有健康检查端点** | 无法监控服务状态 |
| **测试文件零散** | `test1.py`、`test_git.py` 等命名不规范，没有统一的测试框架 |
| **没有 API 版本控制** | 直接 `/api/generate_report`，未来难以演进 |
| **前端代码无构建流程** | 原生 JS，无模块化、无压缩 |

---

## 二、改进后的目录结构

```
12345/
├── app/                              # 🆕 应用核心
│   ├── __init__.py
│   ├── main.py                       # FastAPI 应用工厂
│   │
│   ├── core/                         # 🆕 核心基础设施
│   │   ├── __init__.py
│   │   ├── config.py                 # 统一配置（Pydantic Settings）
│   │   ├── exceptions.py             # 异常体系（错误码 + 分类）
│   │   ├── logging.py                # 日志系统（文件+控制台+轮转+追踪ID）
│   │   └── security.py               # 🆕 安全相关（密钥管理）
│   │
│   ├── api/                          # 🆕 API 路由层
│   │   ├── __init__.py
│   │   ├── deps.py                   # 依赖注入
│   │   ├── middleware.py             # 🆕 中间件（请求ID、耗时统计、异常处理）
│   │   └── v1/                       # API 版本控制
│   │       ├── __init__.py
│   │       ├── router.py             # 路由聚合
│   │       ├── reports.py            # 报告 API
│   │       ├── dify.py               # Dify 代理 API
│   │       └── health.py             # 🆕 健康检查 API
│   │
│   ├── schemas/                      # 🆕 数据模型（替代 models/）
│   │   ├── __init__.py
│   │   ├── base.py                   # 统一响应格式
│   │   ├── common.py                 # 🆕 公共类型（三率、日期范围、分页）
│   │   ├── request.py                # 🆕 请求参数类型
│   │   ├── daily_report.py           # 日报类型
│   │   ├── heating_report.py         # 供暖报告类型
│   │   ├── emergency_report.py       # 紧急报告类型
│   │   ├── annual_analysis.py        # 年度分析类型
│   │   └── custom_period.py          # 自定义时段类型
│   │
│   ├── services/                     # 业务逻辑层（精简后）
│   │   ├── __init__.py
│   │   ├── base.py                   # 🆕 Service 基类
│   │   ├── daily_report.py
│   │   ├── heating_report.py
│   │   ├── emergency_report.py
│   │   ├── annual_analysis.py
│   │   ├── custom_period.py
│   │   └── dify_proxy.py
│   │
│   ├── repositories/                 # 🆕 数据访问层（从 services 分离）
│   │   ├── __init__.py
│   │   ├── base.py                   # Repository 基类 + @with_db 装饰器
│   │   ├── daily_report.py
│   │   ├── heating_report.py
│   │   ├── emergency_report.py
│   │   ├── annual_analysis.py
│   │   └── custom_period.py
│   │
│   ├── mcp/                          # 🆕 MCP 相关（整合）
│   │   ├── __init__.py
│   │   ├── client.py                 # MCPClientWrapper
│   │   ├── servers/                  # MCP 服务器入口
│   │   │   ├── __init__.py
│   │   │   ├── daily.py
│   │   │   ├── heating.py
│   │   │   ├── emergency.py
│   │   │   ├── annual.py
│   │   │   └── custom.py
│   │   └── tools/                    # MCP 工具定义
│   │       ├── __init__.py
│   │       ├── base.py               # 🆕 工具注册基类
│   │       ├── daily.py
│   │       ├── heating.py
│   │       ├── emergency.py
│   │       ├── annual.py
│   │       └── custom.py
│   │
│   └── generators/                   # 🆕 报告生成器（抽象基类）
│       ├── __init__.py
│       ├── base.py                   # 报告生成基类
│       ├── daily.py
│       ├── heating.py
│       ├── emergency.py
│       ├── annual.py
│       └── custom.py
│
├── db/                               # 数据库（保留，增强）
│   ├── __init__.py
│   ├── connection.py                 # 连接池（增加上下文管理器）
│   └── table.py
│
├── tests/                            # 🆕 测试目录（规范化）
│   ├── __init__.py
│   ├── conftest.py                   # pytest fixtures
│   ├── unit/                         # 单元测试
│   │   ├── __init__.py
│   │   ├── test_services/
│   │   ├── test_repositories/
│   │   └── test_schemas/
│   ├── integration/                  # 集成测试
│   │   ├── __init__.py
│   │   └── test_mcp/
│   └── api/                          # API 测试
│       ├── __init__.py
│       └── test_reports.py
│
├── scripts/                          # 脚本
│   ├── start_all.py                  # 🆕 一键启动所有服务
│   ├── stop_all.py                   # 🆕 一键停止
│   └── migration_helper.py
│
├── static/                           # 前端（保留）
├── logs/                             # 🆕 日志目录
├── config/
│   ├── config.yaml                   # 非敏感配置
│   └── .env.example                  # 🆕 环境变量模板
│
├── models/                           # 保留（向后兼容，重导出 schemas）
│   └── __init__.py
│
├── .env                              # 🆕 敏感配置（不提交 git）
├── .gitignore                        # 🆕 更新
├── pyproject.toml                    # 🆕 项目配置
├── web_server.py                     # 保留（向后兼容入口）
└── CLAUDE.md
```

---
## 三、各模块详细改进方案

### 3.1 核心基础设施层 (`app/core/`)

#### 3.1.1 统一配置管理 (`config.py`)

**改进点**：
- 使用 Pydantic Settings 统一管理所有配置
- 敏感信息从 `.env` 文件读取
- 支持类型验证和默认值
- 支持环境变量覆盖

**配置分类**：
```python
class Settings(BaseSettings):
    # 数据库配置
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=3306, alias="DB_PORT")
    db_user: str = Field(alias="DB_USER")
    db_password: str = Field(alias="DB_PASSWORD")
    db_name: str = Field(alias="DB_NAME")
    db_pool_min: int = 1
    db_pool_max: int = 10
    
    # LLM 配置
    llm_api_key: str = Field(alias="LLM_API_KEY")
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "qwen-plus"
    llm_max_tokens: int = 16384
    
    # MCP 服务器端口
    mcp_daily_port: int = 9001
    mcp_heating_port: int = 9002
    mcp_emergency_port: int = 9003
    
    # Dify 配置
    dify_base_url: str = "http://121.43.245.245:5001/v1"
    dify_order_key: str = Field(alias="DIFY_ORDER_KEY")
    
    class Config:
        env_file = ".env"
```

**`.env` 文件示例**：
```bash
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=huairou_12345
LLM_API_KEY=sk-your-api-key-here
DIFY_ORDER_KEY=app-xxx
```

#### 3.1.2 异常处理体系 (`exceptions.py`)

**异常分类**：
```
AppException (基类)
├── ValidationError (1001) - 参数验证错误，HTTP 422
├── NotFoundError (1002) - 资源不存在，HTTP 404
├── DatabaseError (2xxx) - 数据库相关
│   ├── DBConnectionError (2001)
│   ├── DBQueryError (2002)
│   └── DBTimeoutError (2003)
├── LLMError (3xxx) - LLM 调用相关
│   ├── LLMAPIError (3001)
│   ├── LLMRateLimitError (3002)
│   └── LLMTimeoutError (3003)
├── MCPError (4xxx) - MCP 相关
│   ├── MCPConnectionError (4001)
│   └── MCPToolError (4002)
└── BusinessError (5xxx) - 业务逻辑
    ├── InvalidDateError (5001)
    ├── ReportGenerationError (5002)
    └── NoDataFoundError (5003)
```


#### 3.1.3 日志系统 (`logging.py`)

**改进点**：
- 双输出：控制台（可读格式）+ 文件（JSON 格式）
- 日志轮转：按大小（10MB）和数量（保留 5 个）
- 请求追踪 ID：使用 ContextVar 实现
- 错误日志单独文件

**日志格式**：
```
控制台：2025-01-15 10:30:45 | INFO     | [a1b2c3d4] app.services.daily | 开始生成日报
文件JSON：{"timestamp": "...", "level": "INFO", "request_id": "a1b2c3d4", "message": "..."}
```

**实现要点**：
```python
# 请求追踪 ID
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

class JsonFormatter(logging.Formatter):
    """JSON 格式化器"""
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
        })

def setup_logging(log_dir: str = "logs", level: str = "INFO"):
    # 控制台 Handler（可读格式）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ReadableFormatter())
    
    # 文件 Handler（JSON 格式，按大小轮转）
    file_handler = RotatingFileHandler(
        Path(log_dir) / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(JsonFormatter())
```

---

### 3.2 数据模型层 (`app/schemas/`)

#### 3.2.1 公共类型 (`common.py`)

**抽象出的公共类型**：

| 类型 | 说明 | 使用场景 |
|------|------|----------|
| `DateRange` | 日期范围 | 考核周期、查询范围 |
| `DateTimeRange` | 时间范围（精确到秒） | 12小时滚动窗口 |
| `ThreeRatesBase` | 三率基础类型 | 所有涉及三率计算的地方 |
| `RateStats` | 带总量的三率统计 | 日报、考核统计 |
| `AssessmentScore` | 考核成绩（继承三率） | 部门考核排名 |
| `TrendComparison` | 趋势对比 | 环比分析 |
| `RankedItem` | 带排名的条目基类 | Top5、排名列表 |
| `PaginationParams` | 分页参数 | 列表查询 |

**三率计算统一实现**（使用 `@computed_field`）：
```python
class ThreeRatesBase(BaseModel):
    valid: int = Field(0, description="有效回访数", ge=0)
    contact: int = Field(0, description="联系数", ge=0)
    solved: int = Field(0, description="解决数", ge=0)
    satisfied: int = Field(0, description="满意数", ge=0)
    basic_satisfied: int = Field(0, description="基本满意数", ge=0)
    
    @computed_field
    @property
    def response_rate(self) -> float:
        """响应率 = 联系数 / 有效回访数"""
        return round(self.contact / self.valid, 4) if self.valid > 0 else 0.0
    
    @computed_field
    @property
    def solved_rate(self) -> float:
        """解决率 = 解决数 / 有效回访数"""
        return round(self.solved / self.valid, 4) if self.valid > 0 else 0.0
    
    @computed_field
    @property
    def satisfied_rate(self) -> float:
        """满意率 = (满意数 + 0.9 × 基本满意数) / 有效回访数"""
        if self.valid == 0:
            return 0.0
        return round((self.satisfied + 0.9 * self.basic_satisfied) / self.valid, 4)
```

**优势**：
- ✅ 三率计算逻辑统一，不再重复实现
- ✅ 自动计算，无需手动调用 `_calc_rates()`
- ✅ 类型安全，IDE 自动补全
- ✅ 运行时验证，防止数据错误

#### 3.2.2 请求参数类型 (`request.py`)

**新增的请求类型**：

```python
class DailyReportRequest(BaseModel):
    """日报请求"""
    date: date = Field(..., description="报告日期 (YYYY-MM-DD)")
    include_enterprise: bool = Field(True, description="是否包含企业诉求")
    include_assessment: bool = Field(True, description="是否包含考核排名")
    
    @field_validator("date")
    @classmethod
    def validate_date(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("日期不能是未来日期")
        return v

class HeatingReportRequest(BaseModel):
    """供暖报告请求"""
    year: int = Field(..., description="供暖季年度", ge=2020, le=2030)
    include_off_season: bool = Field(False, description="是否包含非供暖季数据")

class CustomPeriodRequest(BaseModel):
    """自定义时段请求"""
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    group_by: Optional[str] = Field("day", description="分组方式: day/week/month")
    
    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("结束日期不能早于开始日期")
        return v
```

#### 3.2.3 统一响应格式 (`base.py`)

```python
class ApiResponse(BaseModel, Generic[T]):
    """统一响应格式"""
    success: bool
    code: str = "0"
    message: str = "ok"
    data: Optional[T] = None
    meta: Optional[ResponseMeta] = None  # request_id, timestamp, duration_ms

    @classmethod
    def ok(cls, data: T = None, message: str = "ok") -> "ApiResponse[T]":
        return cls(success=True, code="0", message=message, data=data)
    
    @classmethod
    def error(cls, code: str, message: str) -> "ApiResponse":
        return cls(success=False, code=code, message=message)

# 向后兼容旧格式
class LegacyResponse(BaseModel):
    """兼容旧版响应格式"""
    status: str  # "success" | "error"
    report: Optional[str] = None
    message: Optional[str] = None
```

#### 3.2.4 TypedDict vs Pydantic 对比

| 方面 | 改进前 (TypedDict) | 改进后 (Pydantic) |
|------|-------------------|-------------------|
| **类型验证** | ❌ 无运行时验证 | ✅ 自动验证 + 错误提示 |
| **默认值** | ❌ 不支持 | ✅ 支持 |
| **计算属性** | ❌ 需手动计算三率 | ✅ 自动计算 (`@computed_field`) |
| **序列化** | ❌ 需手动转换 | ✅ `.model_dump()` / `.model_dump_json()` |
| **API 文档** | ❌ 无 | ✅ 自动生成 OpenAPI 文档 |
| **代码复用** | ❌ 大量重复 | ✅ 继承 + 组合 |
| **IDE 支持** | ⚠️ 有限 | ✅ 完整的类型提示和自动补全 |


---

### 3.3 数据访问层 (`app/repositories/`)

#### 3.3.1 Repository 基类 (`base.py`)

**核心改进**：

```python
# 上下文管理器
@contextmanager
def db_connection():
    conn = None
    try:
        conn = get_connection()
        yield conn
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise DatabaseError(str(e))
    finally:
        if conn:
            release_connection(conn)

# 装饰器 - 自动管理连接
def with_db(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with db_connection() as conn:
            kwargs['conn'] = conn
            return func(*args, **kwargs)
    return wrapper

# 基类
class BaseRepository:
    @with_db
    def execute_query(self, sql: str, params: tuple = None, conn=None) -> list:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    
    @with_db
    def execute_one(self, sql: str, params: tuple = None, conn=None) -> dict:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()
    
    @with_db
    def execute_scalar(self, sql: str, params: tuple = None, conn=None) -> Any:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            result = cur.fetchone()
            return list(result.values())[0] if result else None
```

**优势**：
- ✅ 消除重复的 try/finally 代码
- ✅ 统一异常处理
- ✅ 自动记录查询耗时
- ✅ 支持事务管理

#### 3.3.2 职责分离

**改进前**（Service 层混合数据访问）：
```python
# services/daily_report_service.py
def get_daily_stats_for_date(date_str: str):
    conn = get_connection()
    try:
        sql = "SELECT ... FROM ..."
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
        return _calc_rates(row)  # 业务逻辑
    finally:
        release_connection(conn)
```

**改进后**（职责分离）：
```python
# repositories/daily_report.py
class DailyReportRepository(BaseRepository):
    def get_stats_by_date_range(self, start: datetime, end: datetime) -> dict:
        sql = "SELECT ... FROM ... WHERE 创建时间 >= %s AND 创建时间 < %s"
        return self.execute_one(sql, (start, end))

# services/daily_report.py
class DailyReportService:
    def __init__(self):
        self.repo = DailyReportRepository()
    
    def get_daily_stats(self, date_str: str) -> DailyStatsResult:
        start, end = self._get_noon_range(date_str)
        raw_data = self.repo.get_stats_by_date_range(start, end)
        return DailyStatsResult(**raw_data)  # Pydantic 自动计算三率
```

---

### 3.4 业务逻辑层 (`app/services/`)

#### 3.4.1 Service 基类 (`base.py`)

```python
class BaseService:
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    def validate_date(self, date_str: str) -> date:
        """统一的日期验证"""
        try:
            return parse_date(date_str)
        except ValueError:
            raise InvalidDateError(f"无效日期格式: {date_str}")
    
    def get_noon_range(self, date_str: str) -> Tuple[datetime, datetime]:
        """获取12小时滚动窗口"""
        d = self.validate_date(date_str)
        end_dt = datetime.combine(d, time(12, 0, 0))
        start_dt = end_dt - timedelta(days=1)
        return start_dt, end_dt
    
    def get_assessment_period(self, date_str: str) -> Tuple[date, date]:
        """获取考核周期（19号分界）"""
        d = self.validate_date(date_str)
        if d.day >= 19:
            start = date(d.year, d.month, 19)
        else:
            if d.month == 1:
                start = date(d.year - 1, 12, 19)
            else:
                start = date(d.year, d.month - 1, 19)
        return start, d
```

#### 3.4.2 精简后的 Service 职责

**只负责**：
- 参数验证
- 调用 Repository 获取数据
- 业务逻辑处理（如考核周期计算）
- 组装返回结果

**不再负责**：
- ❌ 数据库连接管理（由 Repository 处理）
- ❌ SQL 查询（由 Repository 处理）
- ❌ 三率计算（由 Pydantic 模型自动计算）


---

### 3.5 报告生成器层 (`app/generators/`)

#### 3.5.1 生成器基类 (`base.py`)

**抽象公共逻辑**：

```python
class BaseReportGenerator(ABC):
    def __init__(self, mcp_url: str, report_type: str):
        self.mcp_url = mcp_url
        self.report_type = report_type
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """返回系统提示词 - 子类必须实现"""
        pass
    
    @abstractmethod
    def build_user_prompt(self, date: str, **kwargs) -> str:
        """构建用户提示词 - 子类必须实现"""
        pass
    
    def validate_date(self, date: str) -> bool:
        """验证日期格式"""
        try:
            datetime.strptime(date, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    
    async def generate(self, date: str, **kwargs) -> str:
        """生成报告（非流式）"""
        if not self.validate_date(date):
            raise ValueError(f"无效的日期格式: {date}")
        
        self.logger.info(f"开始生成 {self.report_type} 报告: {date}")
        
        async with MCPClientWrapper(self.mcp_url) as client:
            system_prompt = self.get_system_prompt()
            user_prompt = self.build_user_prompt(date, **kwargs)
            result = await client.chat(system_prompt, user_prompt)
        
        self.logger.info(f"{self.report_type} 报告生成完成")
        return result
    
    async def generate_stream(self, date: str, **kwargs) -> AsyncGenerator:
        """生成报告（流式）"""
        if not self.validate_date(date):
            yield {"type": "error", "content": f"无效的日期格式: {date}"}
            return
        
        async with MCPClientWrapper(self.mcp_url) as client:
            system_prompt = self.get_system_prompt()
            user_prompt = self.build_user_prompt(date, **kwargs)
            
            async for event in client.chat_stream(system_prompt, user_prompt):
                yield event
```

#### 3.5.2 各报告生成器实现

**只需实现两个方法**：

```python
class DailyReportGenerator(BaseReportGenerator):
    def __init__(self):
        super().__init__(
            mcp_url="http://localhost:9001/daily_report_mcp",
            report_type="daily"
        )
    
    def get_system_prompt(self) -> str:
        return """你是怀柔区12345市民热线的数据分析师..."""
    
    def build_user_prompt(self, date: str, **kwargs) -> str:
        return f"请生成 {date} 的日报..."
```

**优势**：
- ✅ 消除重复代码（3个报告生成器从 ~200 行减少到 ~20 行）
- ✅ 统一的错误处理和日志记录
- ✅ 易于扩展新的报告类型

---

### 3.6 API 层 (`app/api/`)

#### 3.6.1 中间件 (`middleware.py`)

**新增中间件**：

| 中间件 | 功能 |
|--------|------|
| `RequestIDMiddleware` | 生成请求追踪 ID，注入到日志上下文 |
| `TimingMiddleware` | 记录请求耗时 |
| `ExceptionMiddleware` | 统一异常处理，转换为标准响应格式 |
| `LoggingMiddleware` | 记录请求/响应日志 |

```python
class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = (time.time() - start_time) * 1000
        response.headers["X-Process-Time"] = f"{duration:.2f}ms"
        return response
```

#### 3.6.2 依赖注入 (`deps.py`)

```python
def get_db():
    """数据库连接依赖"""
    conn = get_connection()
    try:
        yield conn
    finally:
        release_connection(conn)

def get_settings():
    """配置依赖"""
    return Settings()

def get_daily_service():
    """日报服务依赖"""
    return DailyReportService()
```

#### 3.6.3 API 版本控制

```python
# app/api/v1/router.py
router = APIRouter(prefix="/api/v1")
router.include_router(reports.router, prefix="/reports", tags=["报告"])
router.include_router(dify.router, prefix="/dify", tags=["Dify"])
router.include_router(health.router, prefix="/health", tags=["健康检查"])

# web_server.py - 同时挂载新旧路由
app.include_router(v1_router)  # 新版 /api/v1/...

# 保留旧路由，向后兼容
@app.post("/api/generate_report")
async def legacy_generate_report(...):
    # 内部调用新版 API
    ...
```

#### 3.6.4 健康检查 (`health.py`)

```python
@router.get("/")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@router.get("/ready")
async def readiness_check():
    """就绪检查 - 检查数据库和 MCP 服务"""
    checks = {
        "database": check_database(),
        "mcp_daily": check_mcp_service(9001),
        "mcp_heating": check_mcp_service(9002),
        "mcp_emergency": check_mcp_service(9003),
    }
    all_healthy = all(checks.values())
    return {"ready": all_healthy, "checks": checks}
```


---

### 3.7 MCP 层 (`app/mcp/`)

#### 3.7.1 MCP Client 改进 (`client.py`)

**改进点**：
- 从配置读取 API Key（不再硬编码）
- 增强错误处理和重试逻辑
- 添加超时控制
- 支持连接池

```python
class MCPClientWrapper:
    def __init__(self, mcp_url: str):
        self.mcp_url = mcp_url
        settings = get_settings()
        self.api_key = settings.llm_api_key  # 从配置读取
        self.base_url = settings.llm_base_url
        self.model = settings.llm_model
        self.max_retries = settings.llm_max_retries
```

#### 3.7.2 工具基类 (`tools/base.py`)

```python
class BaseMCPTool:
    """MCP 工具基类"""
    
    def __init__(self, mcp: FastMCP):
        self.mcp = mcp
        self.logger = get_logger(self.__class__.__name__)
    
    def register(self):
        """注册所有工具 - 子类实现"""
        raise NotImplementedError
    
    def handle_error(self, func_name: str, error: Exception) -> dict:
        """统一错误处理"""
        self.logger.error(f"Tool {func_name} error: {error}")
        return {"error": str(error), "success": False}
```

---

### 3.8 测试体系 (`tests/`)

#### 3.8.1 测试框架配置 (`conftest.py`)

```python
@pytest.fixture
def test_settings():
    """测试配置"""
    return Settings(
        db_host="localhost",
        db_name="test_db",
        llm_api_key="test-key",
    )

@pytest.fixture
def mock_db():
    """Mock 数据库"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    
    with patch("db.connection.get_connection", return_value=mock_conn):
        with patch("db.connection.release_connection"):
            yield mock_cursor

@pytest.fixture
def mock_llm():
    """Mock LLM 响应"""
    async def mock_chat(*args, **kwargs):
        return "# 测试报告\n\n这是一份测试报告内容。"
    
    with patch("app.mcp.client.MCPClientWrapper.chat", new=mock_chat):
        yield

@pytest.fixture
def client(app):
    """测试客户端"""
    return TestClient(app)

@pytest.fixture
def data_factory():
    """测试数据工厂"""
    return TestDataFactory()
```

#### 3.8.2 测试分类

| 类型 | 目录 | 说明 | 示例 |
|------|------|------|------|
| 单元测试 | `tests/unit/` | 测试单个函数/类，Mock 外部依赖 | 测试三率计算逻辑 |
| 集成测试 | `tests/integration/` | 测试模块间交互，使用测试数据库 | 测试 Service + Repository |
| API 测试 | `tests/api/` | 测试 HTTP 接口，端到端 | 测试报告生成 API |

#### 3.8.3 测试示例

```python
# tests/unit/test_schemas/test_common.py
def test_three_rates_calculation():
    """测试三率自动计算"""
    rates = ThreeRatesBase(
        valid=100,
        contact=95,
        solved=90,
        satisfied=80,
        basic_satisfied=10
    )
    assert rates.response_rate == 0.95
    assert rates.solved_rate == 0.90
    assert rates.satisfied_rate == 0.89  # (80 + 0.9*10) / 100

# tests/api/test_reports.py
def test_generate_daily_report(client, mock_llm):
    """测试日报生成 API"""
    response = client.post("/api/v1/reports/daily", json={
        "date": "2025-01-15",
        "include_enterprise": True
    })
    assert response.status_code == 200
    assert response.json()["success"] is True
```


---

### 3.9 运维工具 (`scripts/`)

#### 3.9.1 一键启动脚本 (`start_all.py`)

```python
SERVICES = [
    {"name": "MCP-Daily", "cmd": ["python", "-m", "app.mcp.servers.daily"], "port": 9001},
    {"name": "MCP-Heating", "cmd": ["python", "-m", "app.mcp.servers.heating"], "port": 9002},
    {"name": "MCP-Emergency", "cmd": ["python", "-m", "app.mcp.servers.emergency"], "port": 9003},
    {"name": "MCP-Annual", "cmd": ["python", "-m", "app.mcp.servers.annual"], "port": 6001},
    {"name": "MCP-Custom", "cmd": ["python", "-m", "app.mcp.servers.custom"], "port": 6002},
    {"name": "Web-Server", "cmd": ["python", "web_server.py"], "port": 8889},
]

def start_services():
    """启动所有服务"""
    for svc in SERVICES:
        print(f"🚀 启动 {svc['name']} (端口 {svc['port']})...")
        proc = subprocess.Popen(svc["cmd"])
        processes.append({"name": svc["name"], "proc": proc, "port": svc["port"]})
        time.sleep(1)
    
    print("\n✅ 所有服务已启动！")

def stop_services():
    """停止所有服务"""
    print("\n⏹️  正在停止所有服务...")
    for p in processes:
        if p["proc"].poll() is None:
            p["proc"].terminate()
            print(f"  停止 {p['name']}")
```

**使用方式**：
```bash
# 启动所有服务
python scripts/start_all.py

# 停止所有服务（Ctrl+C）
```

#### 3.9.2 项目配置 (`pyproject.toml`)

```toml
[project]
name = "huairou-12345"
version = "1.0.0"
description = "北京市怀柔区 12345 市民热线智能报表生成系统"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "pymysql>=1.1.0",
    "fastmcp>=0.1.0",
    "openai>=1.10.0",
    "httpx>=0.26.0",
    "pyyaml>=6.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "httpx>=0.26.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --cov=app --cov-report=term-missing"

[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I", "N", "UP", "B"]
```

#### 3.9.3 环境变量模板 (`.env.example`)

```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password_here
DB_NAME=huairou_12345

# LLM 配置
LLM_API_KEY=sk-your-api-key-here

# Dify 配置
DIFY_ORDER_KEY=app-your-key-here
DIFY_ELEMENT_KEY=app-your-key-here
DIFY_DISPATCH_KEY=app-your-key-here
DIFY_ADDRESS_KEY=app-your-key-here

# 应用配置
DEBUG=false
LOG_LEVEL=INFO
```

#### 3.9.4 更新 `.gitignore`

```
# 环境变量
.env

# 日志文件
logs/
*.log

# Python
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.coverage

# IDE
.vscode/
.idea/
*.swp
```


---

## 四、实施计划

### 4.1 渐进式迁移策略

采用**渐进式迁移**，每完成一个模块就上线验证，降低风险。

```
阶段 1：基础设施层（不影响现有功能）
   ↓
阶段 2：数据访问层（从 services 分离）
   ↓
阶段 3：报告生成器重构
   ↓
阶段 4：API 层规范化
   ↓
阶段 5：扩展到其他报告类型
   ↓
阶段 6：测试体系 + 运维工具
```

### 4.2 详细实施步骤

#### 阶段 1：基础设施层（2-3 天）

**目标**：建立核心基础设施，不影响现有功能

| 任务 | 文件 | 说明 |
|------|------|------|
| 1. 创建统一配置 | `app/core/config.py` | Pydantic Settings |
| 2. 创建异常体系 | `app/core/exceptions.py` | 错误码 + 分类 |
| 3. 创建日志系统 | `app/core/logging.py` | 文件 + 控制台 + 轮转 |
| 4. 创建环境变量模板 | `.env.example` | 敏感信息管理 |
| 5. 修改 mcp_llm_clint.py | 移除硬编码 API Key | 从配置读取 |
| 6. 修改 web_server.py | 初始化日志系统 | 启动时调用 setup_logging() |

**验证**：
- ✅ 现有服务正常运行
- ✅ 新日志文件生成（logs/app.log）
- ✅ 配置从 .env 正确读取

#### 阶段 2：数据访问层（3-4 天）

**目标**：分离数据访问逻辑，以日报为试点

| 任务 | 文件 | 说明 |
|------|------|------|
| 1. 创建 Repository 基类 | `app/repositories/base.py` | @with_db 装饰器 |
| 2. 创建日报 Repository | `app/repositories/daily_report.py` | 数据访问层 |
| 3. 重构日报 Service | `app/services/daily_report.py` | 调用 Repository |
| 4. 创建公共类型 | `app/schemas/common.py` | ThreeRatesBase 等 |
| 5. 重构日报类型 | `app/schemas/daily_report.py` | 使用 Pydantic |

**验证**：
- ✅ 日报功能正常
- ✅ 三率自动计算正确
- ✅ 数据库连接自动管理

#### 阶段 3：报告生成器重构（2-3 天）

**目标**：抽象报告生成基类，以日报为试点

| 任务 | 文件 | 说明 |
|------|------|------|
| 1. 创建生成器基类 | `app/generators/base.py` | 抽象公共逻辑 |
| 2. 重构日报生成器 | `app/generators/daily.py` | 继承基类 |
| 3. 更新日报 MCP 工具 | `app/mcp/tools/daily.py` | 使用新生成器 |

**验证**：
- ✅ 日报生成功能正常
- ✅ 流式输出正常

#### 阶段 4：API 层规范化（2 天）

**目标**：添加新版 API，保留旧版兼容

| 任务 | 文件 | 说明 |
|------|------|------|
| 1. 创建中间件 | `app/api/middleware.py` | 请求ID、耗时统计 |
| 2. 创建依赖注入 | `app/api/deps.py` | 数据库连接等 |
| 3. 创建 v1 路由 | `app/api/v1/` | 新版 API |
| 4. 创建健康检查 | `app/api/v1/health.py` | /health, /ready |
| 5. 更新 web_server.py | 挂载新路由 | 保留旧路由 |

**验证**：
- ✅ 新旧 API 都能正常工作
- ✅ 健康检查端点可访问
- ✅ 请求追踪 ID 正常

#### 阶段 5：扩展到其他报告类型（3-4 天）

**目标**：将改进应用到所有报告类型

| 任务 | 说明 |
|------|------|
| 1. 供暖报告 | Repository + Service + Generator + Schemas |
| 2. 紧急报告 | Repository + Service + Generator + Schemas |
| 3. 年度分析 | Repository + Service + Generator + Schemas |
| 4. 自定义时段 | Repository + Service + Generator + Schemas |

**验证**：
- ✅ 所有报告类型正常

#### 阶段 6：测试体系 + 运维工具（3-4 天）

**目标**：完善测试和运维

| 任务 | 文件 | 说明 |
|------|------|------|
| 1. 搭建测试框架 | `tests/conftest.py` | pytest fixtures |
| 2. 编写单元测试 | `tests/unit/` | 测试 Service、Repository |
| 3. 编写 API 测试 | `tests/api/` | 测试 HTTP 接口 |
| 4. 一键启动脚本 | `scripts/start_all.py` | 启动所有服务 |
| 5. 项目配置 | `pyproject.toml` | 依赖管理 |

**验证**：
- ✅ 测试覆盖率 > 70%
- ✅ 一键启动脚本正常

### 4.3 时间估算

| 阶段 | 工作量 | 风险 |
|------|--------|------|
| 阶段 1：基础设施层 | 2-3 天 | 低 |
| 阶段 2：数据访问层 | 3-4 天 | 中 |
| 阶段 3：报告生成器 | 2-3 天 | 低 |
| 阶段 4：API 规范化 | 2 天 | 低 |
| 阶段 5：扩展其他类型 | 3-4 天 | 低 |
| 阶段 6：测试 + 运维 | 3-4 天 | 低 |
| **总计** | **15-20 天** | - |


---

## 五、风险评估与注意事项

### 5.1 风险评估

| 风险 | 等级 | 影响 | 缓解措施 |
|------|------|------|----------|
| **API 兼容性破坏** | 🟠 中 | 前端或其他系统调用失败 | 保留旧 API，新旧并存 |
| **数据库连接池耗尽** | 🟡 低 | 服务不可用 | 监控连接数，调整池大小 |
| **LLM API 调用失败** | 🟡 低 | 报告生成失败 | 重试机制 + 降级方案 |
| **日志文件过大** | 🟢 极低 | 磁盘空间不足 | 日志轮转（10MB × 5 个） |
| **测试覆盖不足** | 🟡 低 | 回归问题未发现 | 逐步提高覆盖率 |
| **迁移过程中断** | 🟠 中 | 新旧代码混乱 | 渐进式迁移，每阶段独立 |

### 5.2 向后兼容策略

#### 5.2.1 API 兼容

**保留旧 API 路由**：
```python
# 旧版 API（保留）
@app.post("/api/generate_report")
async def legacy_generate_report(request: dict):
    # 内部调用新版 API
    return await new_generate_report(request)

# 新版 API
@router.post("/api/v1/reports/daily")
async def new_generate_report(request: DailyReportRequest):
    ...
```

#### 5.2.2 Models 兼容

**重导出机制**：
```python
# models/__init__.py（保留，向后兼容）
import warnings
from app.schemas.daily_report import DailyStatsResult, AppealTop5Result

def __getattr__(name):
    warnings.warn(
        f"从 'models' 导入 '{name}' 已弃用，请改用 'app.schemas'",
        DeprecationWarning,
        stacklevel=2
    )
    import app.schemas as schemas
    return getattr(schemas, name, None)
```

### 5.3 注意事项

#### 5.3.1 安全相关

- ⚠️ **立即修复**：移除所有硬编码的 API Key
- ⚠️ **环境变量**：确保 `.env` 文件不提交到 git
- ⚠️ **密钥轮换**：建议更换已暴露的 API Key
- ⚠️ **访问控制**：考虑添加 API 认证（JWT/API Key）

#### 5.3.2 性能相关

- 📊 **数据库连接池**：根据实际负载调整 `db_pool_max`（默认 10）
- 📊 **LLM 超时**：设置合理的超时时间（默认 120 秒）
- 📊 **日志级别**：生产环境使用 INFO，开发环境使用 DEBUG
- 📊 **静态文件**：考虑使用 CDN 或 Nginx 托管

#### 5.3.3 运维相关

- 🔧 **健康检查**：配置监控系统定期检查 `/health/ready`
- 🔧 **日志收集**：考虑使用 ELK 或 Loki 收集日志
- 🔧 **备份策略**：定期备份数据库和配置文件
- 🔧 **回滚方案**：保留旧版代码分支，便于快速回滚

#### 5.3.4 开发相关

- 💻 **代码审查**：每个阶段完成后进行 Code Review
- 💻 **测试先行**：先写测试，再重构代码
- 💻 **文档更新**：及时更新 CLAUDE.md 和 API 文档
- 💻 **依赖管理**：使用 `pyproject.toml` 统一管理依赖

### 5.4 迁移检查清单

#### 阶段 1 完成检查

- [ ] `.env` 文件已创建，包含所有必需的环境变量
- [ ] `.env.example` 已创建，不包含真实密钥
- [ ] `.gitignore` 已更新，排除 `.env` 和 `logs/`
- [ ] `mcp_llm_clint.py` 不再包含硬编码的 API Key
- [ ] 日志文件正常生成（`logs/app.log`）
- [ ] 现有服务正常运行，无功能退化

#### 阶段 2 完成检查

- [ ] `@with_db` 装饰器正常工作
- [ ] 日报 Repository 测试通过
- [ ] 日报 Service 测试通过
- [ ] 三率自动计算正确
- [ ] 数据库连接自动管理，无泄漏

#### 阶段 3 完成检查

- [ ] 报告生成器基类测试通过
- [ ] 日报生成器测试通过
- [ ] 流式输出正常
- [ ] 错误处理正常

#### 阶段 4 完成检查

- [ ] 新版 API (`/api/v1/`) 可访问
- [ ] 旧版 API 仍然正常工作
- [ ] 健康检查端点 (`/health`, `/health/ready`) 可访问
- [ ] 请求追踪 ID 在日志中正常显示
- [ ] 中间件正常工作（耗时统计、异常处理）

#### 阶段 5 完成检查

- [ ] 所有报告类型（日报、供暖、紧急、年度、自定义）正常
- [ ] 所有 MCP 服务器正常启动
- [ ] 所有工具调用正常

#### 阶段 6 完成检查

- [ ] 测试覆盖率 > 70%
- [ ] 所有测试通过
- [ ] 一键启动脚本正常
- [ ] `pyproject.toml` 配置正确
- [ ] 文档已更新

### 5.5 回滚方案

如果迁移过程中出现严重问题，可以按以下步骤回滚：

1. **停止所有服务**
   ```bash
   python scripts/stop_all.py
   ```

2. **切换到旧版代码分支**
   ```bash
   git checkout main-backup
   ```

3. **恢复配置文件**
   ```bash
   cp config/config.yaml.backup config/config.yaml
   ```

4. **重启服务**
   ```bash
   python web_server.py
   # 手动启动各个 MCP 服务器
   ```

---

## 六、总结

### 6.1 改进收益

| 方面 | 改进前 | 改进后 | 收益 |
|------|--------|--------|------|
| **代码行数** | ~4635 行 | ~3500 行（预估） | 减少 25% |
| **重复代码** | 大量重复 | 基本消除 | 提高可维护性 |
| **测试覆盖率** | 0% | > 70% | 提高代码质量 |
| **API 文档** | 无 | 自动生成 | 提高开发效率 |
| **日志系统** | 15 行 | 完整系统 | 提高可观测性 |
| **异常处理** | 3 行 | 完整体系 | 提高稳定性 |
| **启动服务** | 手动 6 次 | 一键启动 | 提高运维效率 |

### 6.2 技术债务清理

- ✅ 消除硬编码的 API Key
- ✅ 统一配置管理
- ✅ 消除重复的三率计算
- ✅ 消除重复的数据库连接管理
- ✅ 消除重复的报告生成逻辑
- ✅ 修复 TypedDict 重复定义

### 6.3 架构提升

- ✅ 清晰的分层架构（API → Service → Repository → DB）
- ✅ 职责分离（数据访问、业务逻辑、API 路由）
- ✅ 依赖注入（便于测试和扩展）
- ✅ 中间件机制（请求追踪、耗时统计、异常处理）
- ✅ 版本控制（API v1，便于未来演进）

### 6.4 下一步建议

完成本次改进后，可以考虑以下进一步优化：

1. **性能优化**
   - 添加 Redis 缓存（缓存报告结果）
   - 数据库查询优化（添加索引）
   - 异步任务队列（Celery）

2. **功能增强**
   - 用户认证和权限管理
   - 报告模板自定义
   - 数据可视化（图表）

3. **运维增强**
   - Docker 容器化
   - CI/CD 流水线
   - 监控告警（Prometheus + Grafana）

---

**文档结束**

