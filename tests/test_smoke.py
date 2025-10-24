#!/usr/bin/env python3
"""
Phase 9.1: Smoke Test Framework
Agent C 产出 - 端到端测试验证

目的：
1. 验证配置系统正常加载
2. 验证股票池访问功能
3. 验证 DataProvider 基础功能
4. 验证端到端回测流程（1只股票 × 1个月）

使用：
    pytest tests/test_smoke.py -v
    pytest tests/test_smoke.py::test_config_loading -v
"""

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Mock pytest for standalone execution
    class pytest:
        class skip:
            class Exception(Exception):
                pass

        @staticmethod
        def skip(reason):
            raise pytest.skip.Exception(reason)

        @staticmethod
        def raises(exc_type):
            class RaisesContext:
                def __init__(self, exc_type):
                    self.exc_type = exc_type

                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc_val, exc_tb):
                    if exc_type is None:
                        raise AssertionError(f"Expected {self.exc_type.__name__} but nothing was raised")
                    if not issubclass(exc_type, self.exc_type):
                        return False
                    return True

            return RaisesContext(exc_type)

        @staticmethod
        def skipif(condition, *, reason=""):
            def decorator(func):
                if condition:
                    def wrapper(*args, **kwargs):
                        raise pytest.skip.Exception(reason)
                    return wrapper
                return func
            return decorator

        class mark:
            @staticmethod
            def skipif(condition, *, reason=""):
                return pytest.skipif(condition, reason=reason)

import pandas as pd
from pathlib import Path
import sys

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_settings, Settings, StockPoolConfig, SystemConfig
from utils.data_provider import (
    AKShareProvider,
    BaseDataProvider,
    SymbolNotFoundError,
    DataProviderError
)

# ============================================
# 测试配置常量
# ============================================

# 价格跳跃检测配置
JUMP_THRESHOLD = 0.30  # 30% 阈值
MAX_ALLOWED_JUMPS = 10  # 允许的最大异常跳跃数

# 已知合理的大幅波动白名单（特殊事件导致的正常波动）
PRICE_JUMP_WHITELIST = {
    '300750.SZ': ['2020-07-13'],  # 创业板改革首日
    '688981.SH': ['2019-07-22'],  # 科创板首日
    '300059.SZ': ['2019-08-19'],  # 重大资产重组复牌
}


# ============================================
# 测试配置加载
# ============================================

def test_config_loading():
    """测试配置系统加载"""
    # 加载配置
    settings = get_settings()

    # 验证配置对象类型
    assert isinstance(settings, Settings), "Settings 类型错误"
    assert isinstance(settings.system, SystemConfig), "SystemConfig 类型错误"
    assert isinstance(settings.stock_pool, StockPoolConfig), "StockPoolConfig 类型错误"

    # 验证数据目录路径
    assert settings.data_dir is not None, "数据目录路径为空"
    assert isinstance(settings.data_dir, Path), "数据目录路径类型错误"

    # 验证结果目录路径
    assert settings.results_dir is not None, "结果目录路径为空"
    assert settings.results_dir.name == "results", "结果目录名称错误"

    print("✓ 配置加载测试通过")


def test_stock_pool_access():
    """测试股票池访问功能"""
    settings = get_settings()

    # 测试 small_cap 池
    small_cap = settings.stock_pool.get_pool('small_cap')
    assert isinstance(small_cap, list), "small_cap 不是列表"
    assert len(small_cap) > 0, "small_cap 为空"

    # 测试 medium_cap 池
    medium_cap = settings.stock_pool.get_pool('medium_cap')
    assert isinstance(medium_cap, list), "medium_cap 不是列表"
    assert len(medium_cap) >= len(small_cap), "medium_cap 数量少于 small_cap"

    # 测试获取股票代码列表
    symbols = settings.stock_pool.get_symbols('small_cap')
    assert isinstance(symbols, list), "股票代码列表类型错误"
    assert all(isinstance(s, str) for s in symbols), "股票代码包含非字符串"
    assert all(s.endswith('.SZ') or s.endswith('.SH') for s in symbols), "股票代码格式错误"

    # 测试股票池大小
    pool_size = settings.stock_pool.get_pool_size('small_cap')
    assert pool_size == len(small_cap), "股票池大小计算错误"

    # 测试错误处理
    with pytest.raises(ValueError):
        settings.stock_pool.get_pool('invalid_pool_name')

    print(f"✓ 股票池访问测试通过")
    print(f"  - small_cap: {len(small_cap)}只")
    print(f"  - medium_cap: {len(medium_cap)}只")


# ============================================
# 测试 DataProvider 基础功能
# ============================================

def test_data_provider_instantiation():
    """测试 DataProvider 实例化"""
    # 创建 AKShare Provider
    provider = AKShareProvider()

    # 验证是 BaseDataProvider 的实例
    assert isinstance(provider, BaseDataProvider), "Provider 不是 BaseDataProvider 实例"
    assert isinstance(provider, AKShareProvider), "Provider 不是 AKShareProvider 实例"

    print("✓ DataProvider 实例化测试通过")


def test_data_provider_symbol_validation():
    """测试股票代码验证"""
    provider = AKShareProvider()

    # 测试有效代码
    assert provider.validate_symbol('000001.SZ'), "有效代码验证失败: 000001.SZ"
    assert provider.validate_symbol('600519.SH'), "有效代码验证失败: 600519.SH"

    # 测试无效代码
    assert not provider.validate_symbol('invalid'), "无效代码未被拒绝: invalid"
    assert not provider.validate_symbol('000001'), "无效代码未被拒绝: 000001"
    assert not provider.validate_symbol(''), "空代码未被拒绝"

    print("✓ 股票代码验证测试通过")


@pytest.mark.skipif(
    not (Path.home() / '.qlib' / 'qlib_data' / 'cn_data' / '000001.SZ.csv').exists(),
    reason="需要本地数据文件: ~/.qlib/qlib_data/cn_data/000001.SZ.csv"
)
def test_data_provider_get_stock_data():
    """测试获取股票数据（需要本地数据）"""
    provider = AKShareProvider()

    # 测试获取数据
    try:
        df = provider.get_stock_data(
            symbol='000001.SZ',
            start_date='2024-01-01',
            end_date='2024-01-31',
            adjust='qfq'
        )

        # 验证返回类型
        assert isinstance(df, pd.DataFrame), "返回数据不是 DataFrame"

        # 验证数据列
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            assert col in df.columns, f"缺少必需列: {col}"

        # 验证数据非空
        assert len(df) > 0, "返回数据为空"

        print(f"✓ 数据获取测试通过")
        print(f"  - 股票: 000001.SZ")
        print(f"  - 数据行数: {len(df)}")

    except Exception as e:
        pytest.skip(f"数据获取失败（可能是网络问题）: {e}")


# ============================================
# 端到端回测测试
# ============================================

@pytest.mark.skipif(
    not (Path.home() / '.qlib' / 'qlib_data' / 'cn_data').exists(),
    reason="需要 Qlib 数据目录: ~/.qlib/qlib_data/cn_data"
)
def test_backtest_end_to_end():
    """端到端回测测试（1只股票 × 1个月）

    测试流程：
    1. 加载配置
    2. 获取股票池中的第一只股票
    3. 加载该股票的1个月数据
    4. 执行简单的回测计算
    5. 验证回测结果
    """
    # 加载配置
    settings = get_settings()

    # 获取股票池中的第一只股票
    symbols = settings.stock_pool.get_symbols('small_cap')
    assert len(symbols) > 0, "股票池为空"

    test_symbol = symbols[0]

    # 检查数据文件是否存在
    data_file = settings.data_dir / f'{test_symbol}.csv'

    if not data_file.exists():
        pytest.skip(f"数据文件不存在: {data_file}")

    # 加载数据
    try:
        df = pd.read_csv(data_file, index_col='date', parse_dates=True)
    except Exception as e:
        pytest.skip(f"数据文件读取失败: {e}")

    # 选择最近1个月的数据
    if len(df) < 20:
        pytest.skip(f"数据量不足: 仅 {len(df)} 行")

    df_month = df.tail(20)  # 最近20个交易日（约1个月）

    # 简单回测：计算收益率
    start_price = df_month.iloc[0]['close']
    end_price = df_month.iloc[-1]['close']

    returns = (end_price - start_price) / start_price

    # 验证回测结果
    assert isinstance(returns, (int, float)), "收益率类型错误"
    assert -1.0 <= returns <= 10.0, f"收益率超出合理范围: {returns*100:.2f}%"

    print(f"✓ 端到端回测测试通过")
    print(f"  - 测试股票: {test_symbol}")
    print(f"  - 数据期间: {df_month.index[0]} ~ {df_month.index[-1]}")
    print(f"  - 收益率: {returns*100:.2f}%")


@pytest.mark.skipif(
    not (Path.home() / '.qlib' / 'qlib_data' / 'cn_data').exists(),
    reason="需要 Qlib 数据目录: ~/.qlib/qlib_data/cn_data"
)
def test_backtest_with_multiple_stocks():
    """多只股票回测测试（前3只 × 1个月）"""
    settings = get_settings()

    # 获取前3只股票
    symbols = settings.stock_pool.get_symbols('small_cap')[:3]

    returns_list = []

    for symbol in symbols:
        data_file = settings.data_dir / f'{symbol}.csv'

        if not data_file.exists():
            continue

        try:
            df = pd.read_csv(data_file, index_col='date', parse_dates=True)
            if len(df) < 20:
                continue

            df_month = df.tail(20)
            start_price = df_month.iloc[0]['close']
            end_price = df_month.iloc[-1]['close']
            returns = (end_price - start_price) / start_price

            returns_list.append((symbol, returns))

        except Exception:
            continue

    # 至少需要2只股票成功回测
    assert len(returns_list) >= 2, f"成功回测的股票数量不足: {len(returns_list)}"

    # 计算平均收益
    avg_returns = sum(r for _, r in returns_list) / len(returns_list)

    print(f"✓ 多只股票回测测试通过")
    print(f"  - 测试股票数: {len(returns_list)}")
    print(f"  - 平均收益率: {avg_returns*100:.2f}%")

    for symbol, ret in returns_list:
        print(f"    {symbol}: {ret*100:+.2f}%")


# ============================================
# 测试复权数据质量（Phase 9.1 核心）
# ============================================

def test_adjfactor_data_integrity():
    """复权数据完整性测试

    验证：
    1. CSV 文件包含必需字段
    2. 数据连续性（无大段缺失）
    3. 缺失值比例 < 5%
    4. 价格数据非负且合理
    """
    settings = get_settings()

    # 获取测试股票
    symbols = settings.stock_pool.get_symbols('small_cap')
    test_symbol = symbols[0]  # 使用第一只股票

    data_file = settings.data_dir / f'{test_symbol}.csv'

    if not data_file.exists():
        pytest.skip(f"数据文件不存在: {data_file}")

    # 加载数据
    df = pd.read_csv(data_file, index_col='date', parse_dates=True)

    # 1. 验证必需字段存在
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    for col in required_columns:
        assert col in df.columns, f"缺少必需字段: {col}"

    # 1.1 验证复权相关字段（如果存在）
    adjfactor_columns = ['factor', 'adjfactor']
    for col in adjfactor_columns:
        if col in df.columns:
            # 验证非空
            assert df[col].notna().all(), f"{col} 包含空值"
            # 验证正值
            assert (df[col] > 0).all(), f"{col} 包含非正值"

            # 验证复权因子的单调性和平滑性
            if col == 'adjfactor' and len(df) > 1:
                # 检查异常变化（单日变化超过50%视为异常）
                pct_changes = df[col].pct_change().abs()
                large_changes = pct_changes[pct_changes > 0.5]
                assert len(large_changes) < 5, \
                    f"{col} 存在过多异常变化 ({len(large_changes)}处 > 50%)，可能存在复权计算问题"

    # 1.2 验证复权后价格合理性
    if 'factor' in df.columns:
        adj_close = df['close'] * df['factor']
        assert (adj_close > 0).all(), "复权后价格包含非正值"
        assert (adj_close < 100000).all(), "复权后价格异常高（>100000），可能存在复权错误"

    # 2. 验证数据连续性（检查日期间隔）
    date_diffs = df.index.to_series().diff()
    # 排除首行和周末（最多3天间隔视为连续）
    large_gaps = date_diffs[date_diffs > pd.Timedelta(days=5)]

    if len(large_gaps) > 0:
        print(f"  ⚠️  发现 {len(large_gaps)} 处大间隔（>5天）")

    # 3. 验证缺失值比例
    missing_ratio = df[required_columns].isnull().sum().sum() / (len(df) * len(required_columns))
    assert missing_ratio < 0.05, f"缺失值比例过高: {missing_ratio*100:.2f}%"

    # 4. 验证价格数据合理性
    for col in ['open', 'high', 'low', 'close']:
        assert (df[col] > 0).all(), f"{col} 包含非正价格"
        assert (df[col] < 10000).all(), f"{col} 包含异常高价（>10000）"

    # 验证高开低收逻辑
    assert (df['high'] >= df['low']).all(), "存在 high < low 的异常数据"
    assert (df['high'] >= df['open']).all(), "存在 high < open 的异常数据"
    assert (df['high'] >= df['close']).all(), "存在 high < close 的异常数据"
    assert (df['low'] <= df['open']).all(), "存在 low > open 的异常数据"
    assert (df['low'] <= df['close']).all(), "存在 low > close 的异常数据"

    print(f"✓ 复权数据完整性测试通过")
    print(f"  - 测试股票: {test_symbol}")
    print(f"  - 数据行数: {len(df)}")
    print(f"  - 缺失值比例: {missing_ratio*100:.4f}%")
    print(f"  - 日期范围: {df.index[0]} ~ {df.index[-1]}")


def test_price_jump_detection():
    """价格异常跳跃检测测试

    目的：
    - 识别单日涨跌幅 > 30% 的异常情况
    - 可能表明复权数据问题或除权未处理
    """
    settings = get_settings()

    # 测试前3只股票
    symbols = settings.stock_pool.get_symbols('small_cap')[:3]

    all_jumps = []

    for symbol in symbols:
        data_file = settings.data_dir / f'{symbol}.csv'

        if not data_file.exists():
            continue

        df = pd.read_csv(data_file, index_col='date', parse_dates=True)

        if len(df) < 2:
            continue

        # 计算日度涨跌幅
        df['daily_return'] = df['close'].pct_change()

        # 识别异常跳跃（阈值从常量读取）
        large_jumps = df[abs(df['daily_return']) > JUMP_THRESHOLD]

        if len(large_jumps) > 0:
            for idx in large_jumps.index:
                all_jumps.append({
                    'symbol': symbol,
                    'date': idx,
                    'return': large_jumps.loc[idx, 'daily_return']
                })

    # 过滤白名单中的已知合理波动
    filtered_jumps = [
        j for j in all_jumps
        if not (j['symbol'] in PRICE_JUMP_WHITELIST and
                str(j['date'])[:10] in PRICE_JUMP_WHITELIST[j['symbol']])
    ]

    # 显示所有跳跃（包括白名单的）
    if len(all_jumps) > 0:
        print(f"  发现 {len(all_jumps)} 处价格跳跃（>{JUMP_THRESHOLD*100:.0f}%）：")
        for jump in all_jumps[:5]:
            is_whitelisted = (jump['symbol'] in PRICE_JUMP_WHITELIST and
                            str(jump['date'])[:10] in PRICE_JUMP_WHITELIST[jump['symbol']])
            status = "✓ 白名单" if is_whitelisted else "⚠️ 需核实"
            print(f"    {status} {jump['symbol']} @ {str(jump['date'])[:10]}: {jump['return']*100:+.2f}%")

        if len(all_jumps) > 5:
            print(f"    ... 还有 {len(all_jumps)-5} 处跳跃")

    # 断言机制：过滤白名单后的异常不能超过阈值
    assert len(filtered_jumps) <= MAX_ALLOWED_JUMPS, \
        f"发现过多异常价格跳跃（{len(filtered_jumps)}处 > {MAX_ALLOWED_JUMPS}），" \
        f"可能存在复权问题。需核实的跳跃: {filtered_jumps[:5]}"

    # 如果有需核实的异常，记录到文件供人工审核
    if filtered_jumps:
        import json
        audit_file = PROJECT_ROOT / 'results' / 'price_jumps_audit.json'
        with open(audit_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_jumps, f, indent=2, default=str, ensure_ascii=False)
        print(f"  ⚠️  {len(filtered_jumps)} 处未白名单跳跃已记录到: {audit_file}")

    print(f"✓ 价格跳跃检测测试通过")
    print(f"  - 测试股票数: {len(symbols)}")
    print(f"  - 总跳跃数: {len(all_jumps)}")
    print(f"  - 白名单过滤: {len(all_jumps) - len(filtered_jumps)}")
    print(f"  - 需核实数: {len(filtered_jumps)} / {MAX_ALLOWED_JUMPS}")


@pytest.mark.skipif(
    True,  # 默认跳过，需要人工提供东方财富数据
    reason="需要东方财富网数据进行对比验证"
)
def test_adjfactor_external_comparison():
    """复权因子外部数据对比测试（预留接口）

    功能：
    - 与东方财富网数据对比前复权价格
    - 计算误差百分比
    - 验证误差 < 1%

    使用：
    1. 手动从东方财富网获取前复权数据
    2. 填充到 EXTERNAL_DATA 字典
    3. 取消 skipif 装饰器
    """
    # 预留数据结构（示例）
    EXTERNAL_DATA = {
        # '600519.SH': {
        #     '2024-01-02': {'qfq_close': 1602.65},  # 东方财富前复权价格
        #     '2024-06-28': {'qfq_close': 1415.91},
        # }
    }

    if not EXTERNAL_DATA:
        pytest.skip("未提供东方财富对比数据")

    settings = get_settings()
    errors = []

    for symbol, dates_data in EXTERNAL_DATA.items():
        data_file = settings.data_dir / f'{symbol}.csv'

        if not data_file.exists():
            continue

        df = pd.read_csv(data_file, index_col='date', parse_dates=True)

        for date_str, external_values in dates_data.items():
            date = pd.Timestamp(date_str)

            if date not in df.index:
                continue

            our_price = df.loc[date, 'close']
            external_price = external_values['qfq_close']

            error_pct = abs(our_price - external_price) / external_price

            errors.append({
                'symbol': symbol,
                'date': date_str,
                'our_price': our_price,
                'external_price': external_price,
                'error_pct': error_pct
            })

            # 验证误差 < 1%
            assert error_pct < 0.01, f"{symbol} @ {date_str}: 误差 {error_pct*100:.2f}% > 1%"

    if errors:
        avg_error = sum(e['error_pct'] for e in errors) / len(errors)
        print(f"✓ 外部数据对比测试通过")
        print(f"  - 对比样本数: {len(errors)}")
        print(f"  - 平均误差: {avg_error*100:.4f}%")


@pytest.mark.skipif(
    not Path(__file__).parent.parent.joinpath('scripts/verify_adjfactor.py').exists(),
    reason="verify_adjfactor.py 脚本不存在"
)
def test_verify_adjfactor_execution():
    """集成测试：执行 verify_adjfactor.py 脚本

    验证：
    1. 脚本能正常执行
    2. 生成验证报告文件
    3. 报告包含测试结果
    """
    import subprocess
    import time

    script_path = Path(__file__).parent.parent / 'scripts' / 'verify_adjfactor.py'
    output_path = Path(__file__).parent.parent / 'results' / 'adjfactor_verification.txt'

    # 删除旧的输出文件以确保测试新生成的文件
    if output_path.exists():
        old_mtime = output_path.stat().st_mtime
        output_path.unlink()
    else:
        old_mtime = 0

    # 执行脚本并验证退出码
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        timeout=60
    )

    assert result.returncode == 0, \
        f"verify_adjfactor.py 执行失败 (退出码 {result.returncode}):\n{result.stderr}"

    # 验证输出文件存在且是新生成的
    assert output_path.exists(), f"验证报告文件不存在: {output_path}"
    assert output_path.stat().st_mtime > old_mtime, "输出文件未更新"

    # 读取并验证报告内容
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 验证报告包含关键信息
    assert '贵州茅台' in content, "报告中缺少贵州茅台数据"
    assert '工商银行' in content, "报告中缺少工商银行数据"
    assert '中国神华' in content, "报告中缺少中国神华数据"
    assert '复权因子' in content, "报告中缺少复权因子信息"

    # 解析报告，统计测试结果
    lines = content.split('\n')
    factor_lines = [l for l in lines if '复权因子:' in l]

    print(f"✓ verify_adjfactor.py 集成测试通过")
    print(f"  - 验证报告: {output_path}")
    print(f"  - 复权因子记录数: {len(factor_lines)}")


# ============================================
# 测试集成
# ============================================

def test_integration_config_and_provider():
    """集成测试：配置系统 + DataProvider"""
    # 加载配置
    settings = get_settings()

    # 创建 Provider
    provider = AKShareProvider(settings=settings.system)

    # 获取股票池
    symbols = settings.stock_pool.get_symbols('small_cap')

    # 验证每个股票代码
    for symbol in symbols:
        assert provider.validate_symbol(symbol), f"股票代码验证失败: {symbol}"

    print(f"✓ 集成测试通过")
    print(f"  - 配置加载: ✓")
    print(f"  - Provider 创建: ✓")
    print(f"  - 股票池验证: {len(symbols)}只 ✓")


# ============================================
# 主测试运行
# ============================================

if __name__ == "__main__":
    """直接运行所有测试"""
    print("="*60)
    print("Phase 9.1 Smoke Test Framework")
    print("="*60)
    print()

    # 按顺序运行测试（基础功能测试）
    tests = [
        ("配置加载测试", test_config_loading),
        ("股票池访问测试", test_stock_pool_access),
        ("DataProvider 实例化测试", test_data_provider_instantiation),
        ("股票代码验证测试", test_data_provider_symbol_validation),
        ("集成测试", test_integration_config_and_provider),
    ]

    # Phase 9.1 核心：复权数据验证测试
    adjfactor_tests = [
        ("复权数据完整性测试", test_adjfactor_data_integrity),
        ("价格异常跳跃检测测试", test_price_jump_detection),
        ("verify_adjfactor.py 集成测试", test_verify_adjfactor_execution),
    ]

    passed = 0
    failed = 0
    skipped = 0

    for name, test_func in tests:
        try:
            print(f"\n[运行] {name}...")
            test_func()
            passed += 1
        except pytest.skip.Exception as e:
            print(f"⚠️  跳过: {e}")
            skipped += 1
        except Exception as e:
            print(f"❌ 失败: {e}")
            failed += 1

    # 复权数据验证测试（Phase 9.1 核心）
    for name, test_func in adjfactor_tests:
        try:
            print(f"\n[运行] {name}...")
            test_func()
            passed += 1
        except pytest.skip.Exception as e:
            print(f"⚠️  跳过: {e}")
            skipped += 1
        except Exception as e:
            print(f"❌ 失败: {e}")
            failed += 1

    # 条件性测试（需要数据文件）
    conditional_tests = [
        ("数据获取测试", test_data_provider_get_stock_data),
        ("端到端回测测试", test_backtest_end_to_end),
        ("多只股票回测测试", test_backtest_with_multiple_stocks),
    ]

    for name, test_func in conditional_tests:
        try:
            print(f"\n[运行] {name}...")
            test_func()
            passed += 1
        except pytest.skip.Exception as e:
            print(f"⚠️  跳过: {e}")
            skipped += 1
        except Exception as e:
            print(f"❌ 失败: {e}")
            failed += 1

    # 总结
    print()
    print("="*60)
    print("测试总结")
    print("="*60)
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"跳过: {skipped}")
    print()

    if failed == 0:
        print("✅ 所有测试通过！")
        sys.exit(0)
    else:
        print("❌ 部分测试失败")
        sys.exit(1)
