"""
AData 数据提供者（占位实现）

AData (1nchaos.com) 是提供A股市场数据的服务，本模块为未来集成预留接口。

当前状态: 占位实现 (Placeholder)
- 所有方法抛出 ProviderNotImplementedError
- 保持接口定义与 BaseDataProvider 一致
- 预留完整的类型注解和文档

未来实现计划:
1. 集成 adata 库 (pip install adata)
2. 实现数据获取逻辑
3. 添加认证和限流处理
4. 支持更多数据类型（财报、资讯等）

使用建议:
目前请使用 AKShareProvider 代替，它提供完整的免费A股数据访问功能。
"""

from typing import Dict, Any
import pandas as pd

from .base import BaseDataProvider
from .exceptions import ProviderNotImplementedError


class ADataProvider(BaseDataProvider):
    """
    AData 数据提供者（占位实现）

    提供与 AData (1nchaos.com) 数据服务的接口，当前为占位实现。

    Example:
        >>> provider = ADataProvider()
        >>> # 以下调用将抛出 ProviderNotImplementedError
        >>> df = provider.get_stock_data('000001.SZ', '2022-01-01', '2024-12-31')
        ProviderNotImplementedError: ADataProvider.get_stock_data is not yet implemented
    """

    def __init__(self, settings=None):
        """
        初始化 AData 提供者

        Args:
            settings: 配置实例（可选）

        Note:
            当前为占位实现，初始化不会执行实际操作
        """
        super().__init__(settings)
        self.logger.warning(
            "ADataProvider is not yet implemented. "
            "Please use AKShareProvider for free A-share data access."
        )

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
            包含OHLCV数据的DataFrame

        Raises:
            ProviderNotImplementedError: 功能未实现

        Note:
            当前为占位实现，请使用 AKShareProvider
        """
        raise ProviderNotImplementedError('ADataProvider', 'get_stock_data')

    def get_index_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        获取指数数据

        Args:
            symbol: 指数代码 (如: 000300.SH=沪深300)
            start_date: 开始日期 (格式: YYYY-MM-DD)
            end_date: 结束日期 (格式: YYYY-MM-DD)

        Returns:
            包含指数数据的DataFrame

        Raises:
            ProviderNotImplementedError: 功能未实现

        Note:
            当前为占位实现，请使用 AKShareProvider
        """
        raise ProviderNotImplementedError('ADataProvider', 'get_index_data')

    def download_to_qlib(
        self,
        symbol: str,
        years: int,
        adjust: str = 'qfq'
    ) -> Dict[str, Any]:
        """
        下载数据并转换为Qlib CSV格式

        Args:
            symbol: 股票代码 (如: 000001.SZ)
            years: 回溯年数
            adjust: 复权类型

        Returns:
            下载结果字典

        Raises:
            ProviderNotImplementedError: 功能未实现

        Note:
            当前为占位实现，请使用 AKShareProvider
        """
        raise ProviderNotImplementedError('ADataProvider', 'download_to_qlib')

    def validate_symbol(self, symbol: str) -> bool:
        """
        验证股票代码格式

        Args:
            symbol: 股票代码 (如: 000001.SZ, 600519.SH)

        Returns:
            True if valid, False otherwise

        Raises:
            ProviderNotImplementedError: 功能未实现

        Note:
            当前为占位实现，请使用 AKShareProvider
        """
        raise ProviderNotImplementedError('ADataProvider', 'validate_symbol')


# 未来实现参考
"""
Future Implementation Reference:

import adata

class ADataProvider(BaseDataProvider):
    def __init__(self, settings=None, token=None):
        super().__init__(settings)
        self.token = token or self.settings.adata.token
        # Initialize adata connection

    def get_stock_data(self, symbol, start_date, end_date, adjust='qfq'):
        # Use adata API to fetch data
        # df = adata.stock.market.get_market(
        #     stock_code=symbol,
        #     start_date=start_date,
        #     end_date=end_date,
        #     adjust=adjust
        # )
        # return self._standardize_dataframe(df)
        pass
"""

__all__ = ['ADataProvider']
