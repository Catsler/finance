"""
数据提供者抽象基类

定义了统一的多数据源接口，所有具体的数据提供者（AKShare、AData、Tushare等）
都必须继承此类并实现其抽象方法。

设计原则:
1. 接口统一: 所有数据源提供一致的API
2. 类型安全: 完整的类型注解
3. 易于扩展: 新增数据源只需实现抽象方法
4. 配置集成: 与Phase 1.2的配置系统无缝集成
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import logging

from config import Settings, get_settings
from .exceptions import (
    InvalidSymbolFormatError,
    DataFormatError,
)


class BaseDataProvider(ABC):
    """
    数据提供者抽象基类

    定义了获取股票数据、指数数据、数据验证和格式转换的统一接口。

    Attributes:
        settings (Settings): 配置实例（来自Phase 1.2配置系统）
        logger (Logger): 日志记录器

    Example:
        >>> class MyProvider(BaseDataProvider):
        ...     def get_stock_data(self, symbol, start_date, end_date, adjust='qfq'):
        ...         # 实现具体逻辑
        ...         pass
        ...
        >>> provider = MyProvider()
        >>> df = provider.get_stock_data('000001.SZ', '2022-01-01', '2024-12-31')
    """

    def __init__(self, settings: Optional[Settings] = None):
        """
        初始化数据提供者

        Args:
            settings: 配置实例（可选，默认使用全局配置）
        """
        self.settings = settings or get_settings()
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def get_stock_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = 'qfq'
    ) -> pd.DataFrame:
        """
        获取股票历史数据

        Args:
            symbol: 股票代码 (如: 000001.SZ, 600519.SH)
            start_date: 开始日期 (格式: YYYY-MM-DD)
            end_date: 结束日期 (格式: YYYY-MM-DD)
            adjust: 复权类型 ('qfq'=前复权, 'hfq'=后复权, ''=不复权)

        Returns:
            包含OHLCV数据的DataFrame，标准列名:
            - date: 日期 (datetime64)
            - open: 开盘价 (float64)
            - high: 最高价 (float64)
            - low: 最低价 (float64)
            - close: 收盘价 (float64)
            - volume: 成交量 (float64)
            - money: 成交额 (float64, 可选)

        Raises:
            SymbolNotFoundError: 股票代码不存在
            DataDownloadError: 数据下载失败
            InvalidSymbolFormatError: 股票代码格式错误

        Example:
            >>> df = provider.get_stock_data('000001.SZ', '2022-01-01', '2024-12-31')
            >>> print(df.columns)
            Index(['date', 'open', 'high', 'low', 'close', 'volume', 'money'], dtype='object')
        """
        pass

    @abstractmethod
    def get_index_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        获取指数数据（如沪深300、中证500等）

        Args:
            symbol: 指数代码 (如: 000300.SH=沪深300, 000905.SH=中证500)
            start_date: 开始日期 (格式: YYYY-MM-DD)
            end_date: 结束日期 (格式: YYYY-MM-DD)

        Returns:
            包含指数数据的DataFrame，标准列名:
            - date: 日期 (datetime64)
            - open: 开盘点位 (float64)
            - high: 最高点位 (float64)
            - low: 最低点位 (float64)
            - close: 收盘点位 (float64)
            - volume: 成交量 (float64)
            - money: 成交额 (float64, 可选)

        Raises:
            SymbolNotFoundError: 指数代码不存在
            DataDownloadError: 数据下载失败

        Example:
            >>> df = provider.get_index_data('000300.SH', '2022-01-01', '2024-12-31')
            >>> print(df['close'].iloc[-1])  # 最新收盘点位
        """
        pass

    @abstractmethod
    def download_to_qlib(
        self,
        symbol: str,
        years: int,
        adjust: str = 'qfq'
    ) -> Dict[str, Any]:
        """
        下载数据并转换为Qlib CSV格式保存

        Args:
            symbol: 股票代码 (如: 000001.SZ)
            years: 回溯年数 (如: 3 表示最近3年)
            adjust: 复权类型 ('qfq'=前复权, 'hfq'=后复权, ''=不复权)

        Returns:
            下载结果字典:
            {
                'symbol': str,           # 股票代码
                'records': int,          # 下载的记录数
                'start_date': str,       # 实际开始日期
                'end_date': str,         # 实际结束日期
                'output_path': str,      # 保存的CSV文件路径
                'status': str,           # 'success' or 'failed'
                'message': str           # 状态消息
            }

        Raises:
            SymbolNotFoundError: 股票代码不存在
            DataDownloadError: 数据下载失败
            DataFormatError: 数据格式错误

        Example:
            >>> result = provider.download_to_qlib('000001.SZ', years=3)
            >>> print(result['records'])  # 下载的记录数
            >>> print(result['output_path'])  # CSV文件路径
        """
        pass

    @abstractmethod
    def validate_symbol(self, symbol: str) -> bool:
        """
        验证股票代码格式是否正确

        Args:
            symbol: 股票代码 (如: 000001.SZ, 600519.SH)

        Returns:
            True if valid, False otherwise

        Example:
            >>> provider.validate_symbol('000001.SZ')  # True
            >>> provider.validate_symbol('000001')     # False
            >>> provider.validate_symbol('000001.XX')  # False
        """
        pass

    # ==================== 辅助方法（子类可选实现） ====================

    def _standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化DataFrame格式（统一列名、数据类型）

        此方法提供了通用的数据标准化逻辑，子类可以覆盖以实现自定义逻辑。

        Args:
            df: 原始数据DataFrame

        Returns:
            标准化后的DataFrame

        Raises:
            DataFormatError: 数据格式不符合预期
        """
        # 必需列检查
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise DataFormatError(
                symbol='unknown',
                issue=f"Missing required columns: {missing_columns}"
            )

        # 确保日期列是datetime类型
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])

        # 确保数值列是float类型
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # 移除NaN值
        df = df.dropna(subset=['close'])

        # 按日期排序
        df = df.sort_values('date').reset_index(drop=True)

        return df

    def _calculate_date_range(self, years: int) -> tuple[str, str]:
        """
        根据回溯年数计算日期范围

        Args:
            years: 回溯年数

        Returns:
            (start_date, end_date) 元组，格式: 'YYYY-MM-DD'

        Example:
            >>> provider._calculate_date_range(3)
            ('2021-10-16', '2024-10-16')  # 假设今天是2024-10-16
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)

        return (
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )

    def _get_qlib_output_path(self, symbol: str) -> Path:
        """
        获取Qlib格式CSV文件的输出路径

        Args:
            symbol: 股票代码 (如: 000001.SZ)

        Returns:
            输出文件的Path对象

        Example:
            >>> path = provider._get_qlib_output_path('000001.SZ')
            >>> print(path)
            PosixPath('/Users/xxx/.qlib/qlib_data/cn_data/000001.SZ.csv')
        """
        data_dir = Path(self.settings.data_dir).expanduser()
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / f"{symbol}.csv"

    def _save_to_qlib_format(
        self,
        df: pd.DataFrame,
        symbol: str
    ) -> str:
        """
        将DataFrame保存为Qlib CSV格式

        Qlib格式要求:
        - 列顺序: date, open, high, low, close, volume, money (可选)
        - 日期格式: YYYY-MM-DD
        - 数值保留2位小数

        Args:
            df: 标准化的DataFrame
            symbol: 股票代码

        Returns:
            保存的CSV文件路径

        Raises:
            DataFormatError: 数据格式不符合Qlib要求
        """
        # 确保列顺序
        base_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        optional_columns = ['money'] if 'money' in df.columns else []
        columns = base_columns + optional_columns

        df_qlib = df[columns].copy()

        # 格式化数值列（保留2位小数）
        numeric_cols = [col for col in columns if col != 'date']
        df_qlib[numeric_cols] = df_qlib[numeric_cols].round(2)

        # 保存到CSV
        output_path = self._get_qlib_output_path(symbol)
        df_qlib.to_csv(output_path, index=False, encoding='utf-8')

        self.logger.info(f"Saved {len(df_qlib)} records to {output_path}")
        return str(output_path)


# 导出抽象基类
__all__ = ['BaseDataProvider']
