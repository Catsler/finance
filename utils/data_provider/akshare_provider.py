"""
AKShare 数据提供者实现

封装 AKShare (akshare.akfamily.xyz) 数据获取逻辑，提供统一的A股数据访问接口。

特性:
- 免费A股数据访问（无需API Key）
- 支持前复权/后复权/不复权
- 自动重试和数据验证
- Qlib格式转换

数据来源: AKShare (https://akshare.akfamily.xyz)
支持数据: A股日线行情、指数数据
"""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import akshare as ak

from .base import BaseDataProvider
from .exceptions import (
    SymbolNotFoundError,
    DataDownloadError,
    InvalidSymbolFormatError,
    DataFormatError,
)


class AKShareProvider(BaseDataProvider):
    """
    AKShare 数据提供者

    封装 AKShare 数据获取逻辑，实现 BaseDataProvider 定义的所有接口。

    Example:
        >>> provider = AKShareProvider()
        >>> df = provider.get_stock_data('000001.SZ', '2022-01-01', '2024-12-31')
        >>> print(df.head())
        >>> result = provider.download_to_qlib('000001.SZ', years=3)
    """

    def __init__(self, settings=None):
        """
        初始化 AKShare 提供者

        Args:
            settings: 配置实例（可选）
        """
        super().__init__(settings)
        self.max_retries = 3
        self.retry_backoff = 2  # 指数退避基数（秒）

    def get_stock_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = 'qfq'
    ) -> pd.DataFrame:
        """
        获取股票历史数据

        使用 AKShare 的 stock_zh_a_hist 接口获取A股日线数据。

        Args:
            symbol: 股票代码 (如: 000001.SZ, 600519.SH)
            start_date: 开始日期 (格式: YYYY-MM-DD)
            end_date: 结束日期 (格式: YYYY-MM-DD)
            adjust: 复权类型 ('qfq'=前复权, 'hfq'=后复权, ''=不复权)

        Returns:
            标准化的DataFrame，列名: date, open, high, low, close, volume, money

        Raises:
            InvalidSymbolFormatError: 股票代码格式错误
            SymbolNotFoundError: 股票代码不存在
            DataDownloadError: 数据下载失败

        Example:
            >>> df = provider.get_stock_data('000001.SZ', '2022-01-01', '2024-12-31')
            >>> print(len(df))  # 约600-700条记录（3年交易日）
        """
        # 验证股票代码格式
        if not self.validate_symbol(symbol):
            raise InvalidSymbolFormatError(symbol)

        # 提取纯数字代码（去掉 .SZ/.SH 后缀）
        code = symbol.replace('.SZ', '').replace('.SH', '')

        # 转换日期格式为 AKShare 要求的 YYYYMMDD
        start_str = start_date.replace('-', '')
        end_str = end_date.replace('-', '')

        # 带重试的数据获取
        for attempt in range(self.max_retries):
            try:
                self.logger.info(
                    f"正在获取 {symbol} 数据（{start_date} ~ {end_date}, adjust={adjust}）..."
                )

                df = ak.stock_zh_a_hist(
                    symbol=code,
                    period='daily',
                    start_date=start_str,
                    end_date=end_str,
                    adjust=adjust,
                )

                if df is None or df.empty:
                    raise SymbolNotFoundError(symbol, 'AKShare')

                # 字段重命名（AKShare 中文列名 → 标准英文列名）
                df = df.rename(columns={
                    '日期': 'date',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume',
                    '成交额': 'money',
                })

                # 标准化数据格式
                df = self._standardize_dataframe(df)

                self.logger.info(f"成功获取 {len(df)} 条记录")
                return df

            except ValueError as e:
                # AKShare 在股票不存在时返回空DataFrame或抛出异常
                if 'not found' in str(e).lower() or 'empty' in str(e).lower():
                    raise SymbolNotFoundError(symbol, 'AKShare') from e
                raise DataDownloadError(symbol, str(e), retry_count=attempt) from e

            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_backoff ** attempt
                    self.logger.warning(
                        f"第 {attempt + 1} 次尝试失败，{wait_time} 秒后重试: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"所有重试失败: {e}")
                    raise DataDownloadError(symbol, str(e), retry_count=attempt) from e

        # 理论上不会执行到这里（循环内已处理所有情况）
        raise DataDownloadError(symbol, "Unknown error after all retries")

    def get_index_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        获取指数数据

        使用 AKShare 的 stock_zh_index_daily 接口获取指数日线数据。

        Args:
            symbol: 指数代码 (如: 000300.SH=沪深300, 000905.SH=中证500)
            start_date: 开始日期 (格式: YYYY-MM-DD)
            end_date: 结束日期 (格式: YYYY-MM-DD)

        Returns:
            标准化的DataFrame

        Raises:
            SymbolNotFoundError: 指数代码不存在
            DataDownloadError: 数据下载失败

        Example:
            >>> df = provider.get_index_data('000300.SH', '2022-01-01', '2024-12-31')
            >>> print(df['close'].iloc[-1])  # 最新收盘点位
        """
        # 指数代码映射（AKShare 使用不同的代码格式）
        index_mapping = {
            '000300.SH': 'sh000300',  # 沪深300
            '000905.SH': 'sh000905',  # 中证500
            '000016.SH': 'sh000016',  # 上证50
            '399006.SZ': 'sz399006',  # 创业板指
        }

        akshare_code = index_mapping.get(symbol)
        if not akshare_code:
            raise SymbolNotFoundError(symbol, 'AKShare')

        # 带重试的数据获取
        for attempt in range(self.max_retries):
            try:
                self.logger.info(
                    f"正在获取指数 {symbol} 数据（{start_date} ~ {end_date}）..."
                )

                df = ak.stock_zh_index_daily(symbol=akshare_code)

                if df is None or df.empty:
                    raise SymbolNotFoundError(symbol, 'AKShare')

                # 字段重命名
                df = df.rename(columns={
                    'date': 'date',
                    'open': 'open',
                    'close': 'close',
                    'high': 'high',
                    'low': 'low',
                    'volume': 'volume',
                })

                # 过滤日期范围
                df['date'] = pd.to_datetime(df['date'])
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]

                # 添加 money 列（指数数据通常没有成交额）
                if 'money' not in df.columns:
                    df['money'] = 0.0

                # 标准化数据格式
                df = self._standardize_dataframe(df)

                self.logger.info(f"成功获取 {len(df)} 条指数记录")
                return df

            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_backoff ** attempt
                    self.logger.warning(
                        f"第 {attempt + 1} 次尝试失败，{wait_time} 秒后重试: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"所有重试失败: {e}")
                    raise DataDownloadError(symbol, str(e), retry_count=attempt) from e

        raise DataDownloadError(symbol, "Unknown error after all retries")

    def download_to_qlib(
        self,
        symbol: str,
        years: int,
        adjust: str = 'qfq'
    ) -> Dict[str, Any]:
        """
        下载数据并转换为Qlib CSV格式

        完整流程: 获取数据 → 验证质量 → 保存CSV

        Args:
            symbol: 股票代码 (如: 000001.SZ)
            years: 回溯年数 (如: 3 表示最近3年)
            adjust: 复权类型 ('qfq'=前复权, 'hfq'=后复权, ''=不复权)

        Returns:
            下载结果字典:
            {
                'symbol': str,
                'records': int,
                'start_date': str,
                'end_date': str,
                'output_path': str,
                'status': 'success' or 'failed',
                'message': str
            }

        Example:
            >>> result = provider.download_to_qlib('000001.SZ', years=3)
            >>> print(result['records'])  # 约750条记录
            >>> print(result['output_path'])  # ~/.qlib/qlib_data/cn_data/000001.SZ.csv
        """
        try:
            # 计算日期范围
            start_date, end_date = self._calculate_date_range(years)

            # 获取数据
            df = self.get_stock_data(symbol, start_date, end_date, adjust)

            # 验证数据质量
            self._validate_dataframe_quality(df, symbol, years)

            # 保存为Qlib格式
            output_path = self._save_to_qlib_format(df, symbol)

            return {
                'symbol': symbol,
                'records': len(df),
                'start_date': df['date'].min().strftime('%Y-%m-%d'),
                'end_date': df['date'].max().strftime('%Y-%m-%d'),
                'output_path': output_path,
                'status': 'success',
                'message': f'Successfully downloaded {len(df)} records'
            }

        except Exception as e:
            self.logger.error(f"下载失败 {symbol}: {e}")
            return {
                'symbol': symbol,
                'records': 0,
                'start_date': '',
                'end_date': '',
                'output_path': '',
                'status': 'failed',
                'message': str(e)
            }

    def validate_symbol(self, symbol: str) -> bool:
        """
        验证股票代码格式

        A股代码格式:
        - 深交所: 6位数字.SZ (如: 000001.SZ, 002475.SZ, 300059.SZ)
        - 上交所: 6位数字.SH (如: 600519.SH, 601318.SH, 688981.SH)

        Args:
            symbol: 股票代码

        Returns:
            True if valid, False otherwise

        Example:
            >>> provider.validate_symbol('000001.SZ')  # True
            >>> provider.validate_symbol('600519.SH')  # True
            >>> provider.validate_symbol('000001')     # False (缺少后缀)
        """
        if not symbol or not isinstance(symbol, str):
            return False

        # 必须以 .SZ 或 .SH 结尾
        if not (symbol.endswith('.SZ') or symbol.endswith('.SH')):
            return False

        # 提取数字部分，必须是6位数字
        code = symbol.split('.')[0]
        if not (code.isdigit() and len(code) == 6):
            return False

        return True

    # ==================== 内部辅助方法 ====================

    def get_intraday_data(
        self,
        symbol: str,
        period: str = '1'
    ) -> pd.DataFrame:
        """
        获取分钟级分时数据

        使用 AKShare 的 stock_zh_a_hist_min_em 接口获取A股分钟K线数据。

        Args:
            symbol: 股票代码 (如: 000001.SZ)
            period: 数据周期 ('1'=1分钟, '5'=5分钟, '15'=15分钟, '30'=30分钟, '60'=60分钟)

        Returns:
            DataFrame with columns: time, open, high, low, close, volume, amount
            按时间升序排列，仅返回当日数据

        Raises:
            InvalidSymbolFormatError: 股票代码格式错误
            SymbolNotFoundError: 股票代码不存在
            DataDownloadError: 数据下载失败
        """
        if not self.validate_symbol(symbol):
            raise InvalidSymbolFormatError(f"Invalid symbol format: {symbol}")

        # Extract code and market
        code, market = symbol.split('.')

        try:
            # Get today's date for filtering
            from datetime import datetime, timedelta
            today = datetime.now().strftime('%Y-%m-%d')
            start_time = f"{today} 09:00:00"
            end_time = f"{today} 15:30:00"

            # Fetch minute data from AKShare
            df = ak.stock_zh_a_hist_min_em(
                symbol=code,
                start_date=start_time,
                end_date=end_time,
                period=period,
                adjust=""  # No adjustment for intraday
            )

            if df is None or df.empty:
                raise SymbolNotFoundError(f"No intraday data for {symbol}")

            # Rename columns to match expected format
            df = df.rename(columns={
                '时间': 'time',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount'
            })

            # Convert time to HH:MM format
            df['time'] = pd.to_datetime(df['time']).dt.strftime('%H:%M')

            # Filter to trading hours only (09:30-15:00)
            df = df[df['time'].between('09:30', '15:00')]

            # Sort by time
            df = df.sort_values('time').reset_index(drop=True)

            return df[['time', 'open', 'high', 'low', 'close', 'volume', 'amount']]

        except Exception as e:
            if "not found" in str(e).lower() or "无数据" in str(e):
                raise SymbolNotFoundError(f"Symbol {symbol} not found or no intraday data")
            raise DataDownloadError(f"Failed to download intraday data for {symbol}: {str(e)}")

    def _validate_dataframe_quality(
        self,
        df: pd.DataFrame,
        symbol: str,
        years: int
    ) -> None:
        """
        验证数据质量

        检查项:
        - 缺失率 < 5%（基于预期交易日数）
        - 所有收盘价 > 0
        - 累计成交量 > 0
        - 无NaN值

        Args:
            df: 待验证的DataFrame
            symbol: 股票代码
            years: 预期年数

        Raises:
            DataFormatError: 数据质量不符合要求
        """
        expected_trading_days_per_year = self.settings.system.data_validation.expected_trading_days_per_year
        expected_trading_days = expected_trading_days_per_year * years
        if expected_trading_days <= 0:
            expected_trading_days = max(1, len(df))
        actual_days = len(df)
        missing_rate = max(0.0, 1 - actual_days / expected_trading_days)

        close_min = df['close'].min()
        close_max = df['close'].max()
        volume_sum = df['volume'].sum()

        self.logger.info(
            f"{symbol} | 记录数={actual_days} | 缺失率={missing_rate*100:.2f}% | "
            f"价格范围=[{close_min:.2f}, {close_max:.2f}] | 总成交量={volume_sum:.0f}"
        )

        # 缺失率：对全市场批量同步场景，以 warning 为主（新股/停牌/数据源缺口都可能导致缺失）
        missing_rate_threshold = self.settings.system.data_validation.missing_rate_threshold
        if missing_rate >= missing_rate_threshold:
            self.logger.warning(
                f"⚠️  {symbol} 缺失率 {missing_rate:.2%} 超过阈值 {missing_rate_threshold:.2%}，仍保存数据供后续审计"
            )

        # 验证规则（硬性错误）
        errors = []

        if close_min <= 0:
            errors.append(f"存在非正收盘价: {close_min}")

        if volume_sum <= 0:
            errors.append("累计成交量为 0")

        # NaN 检查
        nan_counts = df[['open', 'close', 'high', 'low', 'volume']].isna().sum()
        if nan_counts.any():
            errors.append(f"存在 NaN 值: {nan_counts[nan_counts > 0].to_dict()}")

        if errors:
            error_msg = "; ".join(errors)
            self.logger.error(f"✗ {symbol} 验证失败: {error_msg}")
            raise DataFormatError(symbol, error_msg)

        self.logger.info(f"✓ {symbol} 数据验证通过")


__all__ = ['AKShareProvider']
