"""
统一配置管理系统 - 基于Pydantic BaseSettings

用途：
1. 整合config.yaml和stock_pool.yaml
2. 提供类型安全的配置访问
3. 支持环境变量覆盖
4. 为多数据源切换做准备

作者：Claude (AI Agent)
创建日期：2025-10-16
"""

from pathlib import Path
from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml


# ============================================
# 数据模型定义
# ============================================

class StockInfo(BaseModel):
    """股票信息模型"""
    symbol: str = Field(..., description="股票代码 (如 000001.SZ)")
    name: str = Field(..., description="股票名称")
    industry: str = Field(..., description="行业分类")
    sector: str = Field(..., description="细分行业")

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """验证股票代码格式"""
        if not v or len(v) < 9:
            raise ValueError(f"Invalid stock symbol: {v}")
        if not (v.endswith('.SZ') or v.endswith('.SH')):
            raise ValueError(f"Stock symbol must end with .SZ or .SH: {v}")
        return v


class DataValidationConfig(BaseModel):
    """数据验证配置"""
    missing_rate_threshold: float = Field(0.05, description="数据缺失率上限")
    expected_trading_days_per_year: int = Field(252, description="每年交易日数")
    default_years: int = Field(3, description="默认获取年数")


class AKShareConfig(BaseModel):
    """AKShare数据源配置"""
    adjust_type: str = Field("", description="复权类型: ''=不复权, 'qfq'=前复权, 'hfq'=后复权")
    period: str = Field("daily", description="数据周期")
    max_retries: int = Field(3, description="最大重试次数")
    retry_delay: List[int] = Field([2, 4, 8], description="重试延迟(秒)")


class QlibConfig(BaseModel):
    """Qlib数据存储配置"""
    data_root: str = Field("~/.qlib/qlib_data/cn_data", description="数据根目录")
    provider_uri: str = Field("~/.qlib/qlib_data/cn_data", description="Provider URI")
    region: str = Field("cn", description="区域代码")
    storage_format: str = Field("csv", description="存储格式: csv/bin")

    @property
    def data_root_path(self) -> Path:
        """获取扩展后的数据根目录路径"""
        return Path(self.data_root).expanduser()


class LoggingConfig(BaseModel):
    """日志配置"""
    validation_log: str = Field("validation_report.log", description="验证日志文件")
    level: str = Field("INFO", description="日志级别")
    format: str = Field("%(asctime)s [%(levelname)s] %(message)s", description="日志格式")


# ============================================
# 配置主类
# ============================================

class SystemConfig(BaseSettings):
    """系统配置 - 对应config.yaml"""

    # 数据验证
    data_validation: DataValidationConfig = Field(default_factory=DataValidationConfig)

    # 数据源配置
    akshare: AKShareConfig = Field(default_factory=AKShareConfig)
    qlib: QlibConfig = Field(default_factory=QlibConfig)

    # 日志配置
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    # 数据源优先级
    data_source_priority: List[str] = Field(
        default=["AKShare", "AData", "Tushare"],
        description="数据源优先级列表"
    )

    model_config = SettingsConfigDict(
        env_prefix="STOCK_",
        case_sensitive=False,
        extra='ignore'  # 忽略YAML中的额外字段
    )

    @classmethod
    def from_yaml(cls, yaml_path: str = "config.yaml") -> "SystemConfig":
        """从YAML文件加载配置"""
        config_file = Path(yaml_path)
        if not config_file.exists():
            return cls()

        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        return cls(**data)


class StockPoolConfig(BaseSettings):
    """股票池配置 - 对应stock_pool.yaml

    支持的股票池类型：
    - small_cap: 10只股票池（基础池）
    - medium_cap: 20只股票池（继承small_cap + 10只新增）
    - large_cap: 100只股票池（继承medium_cap + 80只新增）- Phase 8.2
    - legacy_test_pool: 长周期测试池（5只2007年前上市的老股）
    """

    # 股票池定义
    small_cap: List[StockInfo] = Field(default_factory=list, description="10只股票池")
    medium_cap: List[StockInfo] = Field(default_factory=list, description="20只股票池")
    large_cap: List[StockInfo] = Field(default_factory=list, description="100只股票池 (Phase 8.2)")
    legacy_test_pool: List[StockInfo] = Field(default_factory=list, description="长周期测试池")

    # 行业配置
    industry_config: Dict[str, List[str]] = Field(default_factory=dict, description="行业分类")

    # 元数据
    version: str = Field("1.0.0", description="配置版本")
    phase: str = Field("Phase 6E", description="当前阶段")

    model_config = SettingsConfigDict(
        env_prefix="STOCK_POOL_",
        case_sensitive=False,
        extra='ignore'
    )

    @classmethod
    def from_yaml(cls, yaml_path: str = "stock_pool.yaml") -> "StockPoolConfig":
        """从YAML文件加载股票池配置

        支持继承机制：
        - small_cap: 基础池
        - medium_cap: 继承small_cap + additional
        - large_cap: 继承medium_cap + additional
        - legacy_test_pool: 独立池
        """
        pool_file = Path(yaml_path)
        if not pool_file.exists():
            return cls()

        with open(pool_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # 处理stock_pools结构
        stock_pools = data.get('stock_pools', {})

        # 处理small_cap（基础池）
        small_cap_raw = stock_pools.get('small_cap', [])
        small_cap = [StockInfo(**stock) for stock in small_cap_raw]

        # 处理medium_cap（继承small_cap + additional）
        medium_cap_config = stock_pools.get('medium_cap', {})
        if isinstance(medium_cap_config, dict):
            medium_cap = small_cap.copy()
            additional = medium_cap_config.get('additional', [])
            medium_cap.extend([StockInfo(**stock) for stock in additional])
        else:
            medium_cap = small_cap.copy()

        # 处理large_cap（继承medium_cap + additional）
        large_cap_config = stock_pools.get('large_cap', {})
        if isinstance(large_cap_config, dict):
            large_cap = medium_cap.copy()
            additional = large_cap_config.get('additional', [])
            # 过滤空列表占位符
            if additional and additional != [[]]:
                large_cap.extend([StockInfo(**stock) for stock in additional])
        else:
            large_cap = medium_cap.copy()

        # 处理legacy_test_pool（独立池）
        legacy_raw = stock_pools.get('legacy_test_pool', [])
        legacy_test_pool = [StockInfo(**stock) for stock in legacy_raw]

        # 提取元数据
        metadata = data.get('_metadata', {})

        return cls(
            small_cap=small_cap,
            medium_cap=medium_cap,
            large_cap=large_cap,
            legacy_test_pool=legacy_test_pool,
            industry_config=data.get('industry_config', {}),
            version=metadata.get('version', '1.0.0'),
            phase=metadata.get('phase', 'Phase 6E')
        )

    def get_pool(self, pool_name: str) -> List[StockInfo]:
        """获取指定股票池

        Args:
            pool_name: 股票池名称，支持：
                - 'small_cap': 10只基础池
                - 'medium_cap': 20只中型池
                - 'large_cap': 100只大型池
                - 'legacy_test_pool': 长周期测试池

        Returns:
            股票信息列表

        Raises:
            ValueError: 如果pool_name不存在
        """
        if not hasattr(self, pool_name):
            valid_pools = ['small_cap', 'medium_cap', 'large_cap', 'legacy_test_pool']
            raise ValueError(
                f"未知的股票池名称: {pool_name}. "
                f"支持的池: {', '.join(valid_pools)}"
            )
        return getattr(self, pool_name, [])

    def get_symbols(self, pool_name: str) -> List[str]:
        """获取指定股票池的代码列表

        Args:
            pool_name: 股票池名称

        Returns:
            股票代码列表
        """
        pool = self.get_pool(pool_name)
        return [stock.symbol for stock in pool]

    def get_pool_size(self, pool_name: str) -> int:
        """获取指定股票池的大小

        Args:
            pool_name: 股票池名称

        Returns:
            股票数量
        """
        return len(self.get_pool(pool_name))


class BacktestConfig(BaseModel):
    """回测参数配置"""

    # 选股策略参数
    momentum_threshold: float = Field(0.0, description="动量阈值(%)")
    ma_short: int = Field(5, description="短期均线周期")
    ma_long: int = Field(10, description="长期均线周期")
    top_n_stocks: int = Field(20, description="选股数量")

    # 调仓频率
    rebalance_freq: Literal['monthly', 'quarterly', 'yearly'] = Field(
        'monthly',
        description="调仓频率"
    )

    # 交易成本
    commission_rate: float = Field(0.00115, description="佣金率")
    slippage_rate: float = Field(0.00215, description="滑点率")

    # 风控参数
    stop_loss: Optional[float] = Field(None, description="止损阈值(%)")
    trailing_stop: Optional[float] = Field(None, description="跟踪止损阈值(%)")
    take_profit: Optional[List[float]] = Field(None, description="止盈阶梯")

    # 初始资金
    initial_capital: float = Field(100000.0, description="初始资金(元)")


# ============================================
# 全局配置实例
# ============================================

class Settings(BaseSettings):
    """全局配置管理器"""

    system: SystemConfig = Field(default_factory=SystemConfig)
    stock_pool: StockPoolConfig = Field(default_factory=StockPoolConfig)
    backtest: BacktestConfig = Field(default_factory=BacktestConfig)

    # 项目路径
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent)

    model_config = SettingsConfigDict(
        env_prefix="STOCK_APP_",
        case_sensitive=False,
        extra='ignore'
    )

    @classmethod
    def load(
        cls,
        config_yaml: str = "config.yaml",
        pool_yaml: str = "stock_pool.yaml"
    ) -> "Settings":
        """
        加载完整配置

        Args:
            config_yaml: 系统配置文件路径
            pool_yaml: 股票池配置文件路径

        Returns:
            Settings实例
        """
        project_root = Path(__file__).parent.parent

        # 加载系统配置
        config_path = project_root / config_yaml
        system_config = SystemConfig.from_yaml(str(config_path))

        # 加载股票池配置
        pool_path = project_root / pool_yaml
        pool_config = StockPoolConfig.from_yaml(str(pool_path))

        return cls(
            system=system_config,
            stock_pool=pool_config,
            project_root=project_root
        )

    @property
    def data_dir(self) -> Path:
        """获取数据目录路径"""
        return self.system.qlib.data_root_path

    @property
    def results_dir(self) -> Path:
        """获取结果目录路径"""
        return self.project_root / "results"

    @property
    def scripts_dir(self) -> Path:
        """获取脚本目录路径"""
        return self.project_root / "scripts"


# ============================================
# 便捷函数
# ============================================

def get_settings() -> Settings:
    """
    获取全局配置实例（单例模式）

    Returns:
        Settings实例
    """
    if not hasattr(get_settings, '_instance'):
        get_settings._instance = Settings.load()
    return get_settings._instance


def reload_settings() -> Settings:
    """
    重新加载配置（用于配置文件更新后）

    Returns:
        新的Settings实例
    """
    if hasattr(get_settings, '_instance'):
        delattr(get_settings, '_instance')
    return get_settings()


# ============================================
# 使用示例
# ============================================

if __name__ == "__main__":
    # 加载配置
    settings = get_settings()

    # 访问系统配置
    print(f"数据根目录: {settings.system.qlib.data_root}")
    print(f"数据源优先级: {settings.system.data_source_priority}")

    # 访问股票池
    print(f"\n小盘股票池 ({len(settings.stock_pool.small_cap)}只):")
    for stock in settings.stock_pool.small_cap[:3]:
        print(f"  - {stock.symbol} {stock.name} ({stock.industry})")

    print(f"\n中盘股票池 ({len(settings.stock_pool.medium_cap)}只):")
    for stock in settings.stock_pool.medium_cap[:3]:
        print(f"  - {stock.symbol} {stock.name} ({stock.industry})")

    print(f"\n大盘股票池 ({len(settings.stock_pool.large_cap)}只) - Phase 8.2:")
    for stock in settings.stock_pool.large_cap[:3]:
        print(f"  - {stock.symbol} {stock.name} ({stock.industry})")
    print(f"  ... (当前继承自medium_cap，等待Agent L新增80只)")

    # 访问回测配置
    print(f"\n回测配置:")
    print(f"  - 动量阈值: {settings.backtest.momentum_threshold}%")
    print(f"  - MA周期: {settings.backtest.ma_short}/{settings.backtest.ma_long}")
    print(f"  - 调仓频率: {settings.backtest.rebalance_freq}")
    print(f"  - 佣金率: {settings.backtest.commission_rate*100}%")

    # 访问路径
    print(f"\n项目路径:")
    print(f"  - 项目根目录: {settings.project_root}")
    print(f"  - 数据目录: {settings.data_dir}")
    print(f"  - 结果目录: {settings.results_dir}")
