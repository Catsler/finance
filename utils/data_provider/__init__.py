"""
DataProvider 数据提供者抽象层

支持多数据源统一接口，便于在 AKShare、AData、Tushare 等数据源之间切换。

## 核心组件

- **BaseDataProvider**: 抽象基类，定义统一的数据访问接口
- **异常体系**: 完整的异常层次结构，便于错误处理和诊断

## 使用示例

```python
from utils.data_provider import AKShareProvider, SymbolNotFoundError

# 创建数据提供者实例
provider = AKShareProvider()

# 获取股票数据
try:
    df = provider.get_stock_data(
        symbol='000001.SZ',
        start_date='2022-01-01',
        end_date='2024-12-31',
        adjust='qfq'  # 前复权
    )
except SymbolNotFoundError as e:
    print(f"股票不存在: {e.symbol}")
```

## 数据源支持

- ✅ **AKShare**: 免费A股数据（已实现）
- 🔜 **AData**: 1nchaos数据源（占位）
- 🔜 **Tushare**: 专业数据服务（未来支持）

## 设计原则

1. **接口统一**: 所有数据源实现相同的抽象接口
2. **易于扩展**: 新增数据源只需继承 BaseDataProvider
3. **类型安全**: 完整的类型注解，IDE友好
4. **错误明确**: 清晰的异常体系，便于调试
"""

from .base import BaseDataProvider
from .exceptions import (
    DataProviderError,
    SymbolNotFoundError,
    DataDownloadError,
    InvalidSymbolFormatError,
    DataFormatError,
    ProviderNotImplementedError,
)
from .akshare_provider import AKShareProvider
from .adata_provider import ADataProvider

__all__ = [
    # 抽象基类
    'BaseDataProvider',

    # 具体实现
    'AKShareProvider',
    'ADataProvider',

    # 异常类
    'DataProviderError',
    'SymbolNotFoundError',
    'DataDownloadError',
    'InvalidSymbolFormatError',
    'DataFormatError',
    'ProviderNotImplementedError',
]

__version__ = '1.0.0'
__author__ = 'Stock Trading System'
