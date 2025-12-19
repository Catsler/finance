"""
数据提供者异常体系

定义了完整的异常层次结构，用于数据获取、验证、转换过程中的错误处理。

异常层次:
    DataProviderError (基础异常)
    ├── SymbolNotFoundError (股票代码不存在)
    ├── DataDownloadError (数据下载失败)
    ├── InvalidSymbolFormatError (股票代码格式错误)
    ├── DataFormatError (数据格式错误)
    └── ProviderNotImplementedError (功能未实现)
"""

from typing import Optional


class DataProviderError(Exception):
    """
    数据提供者基础异常

    所有数据提供者相关的异常都应继承此类。
    """
    pass


class SymbolNotFoundError(DataProviderError):
    """
    股票代码不存在异常

    当请求的股票代码在数据源中不存在时抛出。

    Attributes:
        symbol (str): 不存在的股票代码
        provider (str): 数据提供者名称

    Example:
        >>> raise SymbolNotFoundError('999999.SH', 'AKShare')
        SymbolNotFoundError: Symbol 999999.SH not found in AKShare
    """

    def __init__(self, symbol: str, provider: str):
        self.symbol = symbol
        self.provider = provider
        super().__init__(
            f"Symbol {symbol} not found in {provider}. "
            f"Please check if the symbol exists and is in correct format."
        )


class DataDownloadError(DataProviderError):
    """
    数据下载失败异常

    当从数据源下载数据失败时抛出（网络错误、API限流等）。

    Attributes:
        symbol (str): 尝试下载的股票代码
        reason (str): 失败原因描述
        retry_count (int): 已重试次数（可选）

    Example:
        >>> raise DataDownloadError('000001.SZ', 'Network timeout', retry_count=3)
        DataDownloadError: Failed to download 000001.SZ: Network timeout (retried 3 times)
    """

    def __init__(self, symbol: str, reason: str, retry_count: Optional[int] = None):
        self.symbol = symbol
        self.reason = reason
        self.retry_count = retry_count

        msg = f"Failed to download {symbol}: {reason}"
        if retry_count is not None:
            msg += f" (retried {retry_count} times)"

        super().__init__(msg)


class InvalidSymbolFormatError(DataProviderError):
    """
    股票代码格式错误异常

    当股票代码不符合预期格式时抛出。

    Attributes:
        symbol (str): 格式错误的股票代码
        expected_format (str): 期望的格式说明

    Example:
        >>> raise InvalidSymbolFormatError('000001', 'XXXXXX.SZ or XXXXXX.SH')
        InvalidSymbolFormatError: Invalid symbol format: 000001. Expected: XXXXXX.SZ or XXXXXX.SH
    """

    def __init__(self, symbol: str, expected_format: str = 'XXXXXX.SZ or XXXXXX.SH'):
        self.symbol = symbol
        self.expected_format = expected_format
        super().__init__(
            f"Invalid symbol format: {symbol}. "
            f"Expected: {expected_format}"
        )


class DataFormatError(DataProviderError):
    """
    数据格式错误异常

    当下载的数据格式不符合预期时抛出（缺少必需列、数据类型错误等）。

    Attributes:
        symbol (str): 相关的股票代码
        issue (str): 格式问题描述

    Example:
        >>> raise DataFormatError('000001.SZ', 'Missing required column: close')
        DataFormatError: Data format error for 000001.SZ: Missing required column: close
    """

    def __init__(self, symbol: str, issue: str):
        self.symbol = symbol
        self.issue = issue
        super().__init__(
            f"Data format error for {symbol}: {issue}"
        )


class ProviderNotImplementedError(DataProviderError):
    """
    数据提供者功能未实现异常

    当调用的功能尚未实现时抛出（占位类、待开发功能）。

    Attributes:
        provider (str): 数据提供者名称
        feature (str): 未实现的功能名称（可选）

    Example:
        >>> raise ProviderNotImplementedError('ADataProvider', 'get_stock_data')
        ProviderNotImplementedError: ADataProvider.get_stock_data is not yet implemented
    """

    def __init__(self, provider: str, feature: Optional[str] = None):
        self.provider = provider
        self.feature = feature

        if feature:
            msg = f"{provider}.{feature} is not yet implemented. "
        else:
            msg = f"{provider} is not yet implemented. "

        msg += "Please use AKShareProvider or check future releases."

        super().__init__(msg)


# 导出所有异常类，便于模块级别导入
__all__ = [
    'DataProviderError',
    'SymbolNotFoundError',
    'DataDownloadError',
    'InvalidSymbolFormatError',
    'DataFormatError',
    'ProviderNotImplementedError',
]
