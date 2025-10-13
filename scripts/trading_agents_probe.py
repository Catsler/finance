#!/usr/bin/env python3
"""
Phase 9A: TradingAgents AI探针 - 最小可行单元

功能：
- 读取 phase6d 真实回测结果
- 调用 gpt-4.1-mini 对股票进行技术分析评分
- 输出 AI评分 vs 实际收益对比

用法：
    python scripts/trading_agents_probe.py
    python scripts/trading_agents_probe.py --max-samples 5
    python scripts/trading_agents_probe.py --config config/ai_agents_local.yaml
"""

import os
import sys
import re
import yaml
import pandas as pd
import numpy as np
import argparse
import json
from pathlib import Path
from datetime import datetime
import logging

# 导入 OpenAI（兼容最新版本）
try:
    from openai import OpenAI
except ImportError:
    print("❌ 错误：未安装 openai 库")
    print("请运行：pip install openai")
    sys.exit(1)


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path='config/ai_agents.yaml'):
    """
    加载配置文件，支持环境变量替换

    优先级：ai_agents_local.yaml > ai_agents.yaml
    """
    # 尝试本地配置
    local_config_path = config_path.replace('.yaml', '_local.yaml')
    if os.path.exists(local_config_path):
        config_path = local_config_path
        logger.info(f"✓ 使用本地配置: {local_config_path}")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 环境变量替换
    api_key = config['openai']['api_key']
    if api_key.startswith('${') and api_key.endswith('}'):
        env_var = api_key[2:-1]
        api_key = os.getenv(env_var)
        if not api_key:
            raise ValueError(
                f"环境变量 {env_var} 未设置\n"
                f"请运行: export {env_var}=your_api_key"
            )
        config['openai']['api_key'] = api_key

    logger.info(f"✓ 配置加载成功: {config_path}")
    return config


def load_stock_pool(pool_path='stock_pool.yaml'):
    """
    加载股票池，提取股票元信息

    Returns:
        dict: {symbol: {name, industry, sector}}
    """
    if not os.path.exists(pool_path):
        raise FileNotFoundError(f"股票池文件不存在: {pool_path}")

    with open(pool_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    stock_info = {}

    # 处理 medium_cap（包含 inherit_from）
    if 'medium_cap' in data['stock_pools']:
        pool = data['stock_pools']['medium_cap']

        # 继承 small_cap
        if pool.get('inherit_from') == 'small_cap':
            for stock in data['stock_pools']['small_cap']:
                stock_info[stock['symbol']] = {
                    'name': stock['name'],
                    'industry': stock['industry'],
                    'sector': stock['sector']
                }

        # 添加额外股票
        if 'additional' in pool:
            for stock in pool['additional']:
                stock_info[stock['symbol']] = {
                    'name': stock['name'],
                    'industry': stock['industry'],
                    'sector': stock['sector']
                }

    # 兜底：加载 small_cap
    if not stock_info and 'small_cap' in data['stock_pools']:
        for stock in data['stock_pools']['small_cap']:
            stock_info[stock['symbol']] = {
                'name': stock['name'],
                'industry': stock['industry'],
                'sector': stock['sector']
            }

    logger.info(f"✓ 股票池加载成功: {len(stock_info)}只股票")
    return stock_info


def calculate_ma(symbol, date, period=5, data_dir='~/.qlib/qlib_data/cn_data'):
    """
    计算移动平均线（从Qlib数据）

    Args:
        symbol: 股票代码
        date: 目标日期（pd.Timestamp）
        period: MA周期
        data_dir: Qlib数据目录

    Returns:
        float: MA值，如果失败返回None
    """
    try:
        data_dir = os.path.expanduser(data_dir)
        file_path = os.path.join(data_dir, f'{symbol}.csv')

        if not os.path.exists(file_path):
            logger.warning(f"⚠️  数据文件不存在: {file_path}")
            return None

        df = pd.read_csv(file_path)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()

        # 找到目标日期或之前最近的交易日
        available_dates = df.index[df.index <= date]
        if len(available_dates) == 0:
            return None

        target_date = available_dates[-1]

        # 计算MA
        end_idx = df.index.get_loc(target_date)
        start_idx = max(0, end_idx - period + 1)

        if end_idx - start_idx + 1 < period:
            return None

        ma_value = df.iloc[start_idx:end_idx + 1]['close'].mean()
        return round(ma_value, 2)

    except Exception as e:
        logger.warning(f"⚠️  计算 MA{period} 失败 ({symbol}): {e}")
        return None


def parse_ai_score(content):
    """
    增强的AI评分解析，支持多种格式

    支持格式：
    - "8分"
    - "评分：8" 或 "评分: 8"
    - "8/10"
    - "8. 理由..."

    Args:
        content: AI返回的文本内容

    Returns:
        int: 评分（1-10），解析失败返回None
    """
    patterns = [
        r'(\d+)\s*分',              # "8分"
        r'评分[：:]\s*(\d+)',        # "评分：8" 或 "评分: 8"
        r'(\d+)\s*/\s*10',           # "8/10"
        r'^(\d+)[\s\.\|]',           # 开头数字如 "8. 理由..."
    ]

    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            score = int(match.group(1))
            if 1 <= score <= 10:
                return score

    logger.warning(f"⚠️  无法解析评分: {content[:50]}...")
    return None


def analyze_stock_with_ai(context, config):
    """
    调用 OpenAI API 分析股票

    Args:
        context: dict {symbol, name, momentum_20d, ma5, ma10, industry, sector}
        config: 配置字典

    Returns:
        dict: {ai_score, ai_reason, cost_usd, success}
    """
    try:
        client = OpenAI(
            api_key=config['openai']['api_key'],
            base_url=config['openai']['base_url']
        )

        # 构造prompt
        prompt_template = config['agents']['technical_analyst']['prompt_template']
        prompt = prompt_template.format(**context)

        # 调用API
        response = client.chat.completions.create(
            model=config['openai']['model'],
            messages=[{"role": "user", "content": prompt}],
            temperature=config['openai']['temperature'],
            max_tokens=config['openai']['max_tokens'],
            timeout=config['openai'].get('timeout', 10)
        )

        # 解析响应
        content = response.choices[0].message.content.strip()
        usage = response.usage

        # 计算成本（gpt-4.1-mini: $0.15/1M input, $0.60/1M output）
        cost_usd = (
            usage.prompt_tokens * 0.00015 / 1000 +
            usage.completion_tokens * 0.0006 / 1000
        )

        # 提取评分（使用增强的解析函数）
        ai_score = parse_ai_score(content)

        # 提取理由（去除评分部分，保留理由）
        ai_reason = re.sub(r'.*?(\d+)\s*[分/:].*?[:：]?\s*', '', content)
        ai_reason = ai_reason.replace('\n', ' ').strip()[:50]  # 限制长度

        logger.info(f"  ✓ {context['symbol']}: 评分={ai_score}, 成本=${cost_usd:.6f}")

        return {
            'ai_score': ai_score,
            'ai_reason': ai_reason,
            'cost_usd': cost_usd,
            'success': True
        }

    except Exception as e:
        logger.error(f"  ❌ {context.get('symbol', 'unknown')}: {e}")
        return {
            'ai_score': None,
            'ai_reason': f"API错误: {str(e)[:30]}",
            'cost_usd': 0.0,
            'success': False
        }


def main():
    parser = argparse.ArgumentParser(description='Phase 9A: AI探针分析')
    parser.add_argument('--config', default='config/ai_agents.yaml',
                       help='配置文件路径')
    parser.add_argument('--max-samples', type=int, default=None,
                       help='最大分析股票数（默认：配置文件中的值）')
    parser.add_argument('--backtest-file', default='results/phase6d_profit_distribution.csv',
                       help='回测结果文件')
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("Phase 9A: TradingAgents AI探针启动")
    logger.info("=" * 70)

    # 1. 加载配置
    config = load_config(args.config)
    max_samples = args.max_samples or config['probe']['max_samples']

    # 2. 加载股票池
    stock_info = load_stock_pool()

    # 3. 加载回测结果
    if not os.path.exists(args.backtest_file):
        raise FileNotFoundError(f"回测结果文件不存在: {args.backtest_file}")

    backtest_df = pd.read_csv(args.backtest_file)
    backtest_df['start_date'] = pd.to_datetime(backtest_df['start_date'])
    backtest_df['end_date'] = pd.to_datetime(backtest_df['end_date'])

    logger.info(f"✓ 回测数据加载: {len(backtest_df)}条记录")

    # 4. 采样（取前N条）
    sample_df = backtest_df.head(max_samples).copy()
    logger.info(f"✓ 采样数量: {len(sample_df)}条")
    logger.info("")

    # 5. 逐条分析
    results = []
    total_cost = 0.0

    for idx, row in sample_df.iterrows():
        symbol = row['symbol']

        # 获取股票元信息
        info = stock_info.get(symbol, {
            'name': symbol,
            'industry': '未知',
            'sector': '未知'
        })

        # 计算MA（使用持仓期结束日期）
        ma5 = calculate_ma(symbol, row['end_date'], period=5)
        ma10 = calculate_ma(symbol, row['end_date'], period=10)

        # 如果MA计算失败，跳过
        if ma5 is None or ma10 is None:
            logger.warning(f"  ⚠️  {symbol}: MA数据不足，跳过")
            continue

        # 构造分析上下文
        context = {
            'symbol': symbol,
            'name': info['name'],
            'momentum_20d': row['return_pct'] / 100,  # 转换为小数
            'ma5': ma5,
            'ma10': ma10,
            'industry': info['industry'],
            'sector': info['sector']
        }

        # 调用AI分析
        ai_result = analyze_stock_with_ai(context, config)

        # 汇总结果
        results.append({
            'symbol': symbol,
            'name': info['name'],
            'period_start': row['start_date'].strftime('%Y-%m-%d'),
            'period_end': row['end_date'].strftime('%Y-%m-%d'),
            'momentum_20d': row['return_pct'],
            'ma5': ma5,
            'ma10': ma10,
            'ai_score': ai_result['ai_score'],
            'ai_reason': ai_result['ai_reason'],
            'actual_return': row['return_pct'],
            'cost_usd': ai_result['cost_usd']
        })

        total_cost += ai_result['cost_usd']

    # 6. 输出CSV
    if not results:
        logger.error("❌ 没有成功分析的数据")
        sys.exit(1)

    result_df = pd.DataFrame(results)
    csv_path = config['output']['csv_path']
    result_df.to_csv(csv_path, index=False, encoding='utf-8')
    logger.info("")
    logger.info(f"✓ CSV输出: {csv_path}")

    # 7. 生成汇总JSON
    summary = {
        'total_samples': len(results),
        'success_count': sum(1 for r in results if r['ai_score'] is not None),
        'total_cost_usd': round(total_cost, 6),
        'avg_cost_per_sample': round(total_cost / len(results), 6),
        'ai_score_stats': {
            'mean': round(result_df['ai_score'].mean(), 2),
            'std': round(result_df['ai_score'].std(), 2),
            'min': int(result_df['ai_score'].min()),
            'max': int(result_df['ai_score'].max())
        },
        'correlation': {
            'ai_score_vs_return': round(
                result_df['ai_score'].corr(result_df['actual_return']), 3
            ) if len(result_df) > 1 else None,
            'sample_size': len(result_df),
            'warning': '⚠️ 样本量<20，相关性仅供参考，不具统计显著性' if len(result_df) < 20 else None
        },
        'config': {
            'model': config['openai']['model'],
            'max_samples': max_samples,
            'backtest_file': args.backtest_file
        },
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    summary_path = config['output']['summary_path']
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    logger.info(f"✓ JSON汇总: {summary_path}")
    logger.info("")
    logger.info("=" * 70)
    logger.info("📊 分析汇总")
    logger.info("=" * 70)
    logger.info(f"总样本数: {summary['total_samples']}")
    logger.info(f"成功数: {summary['success_count']}")
    logger.info(f"总成本: ${summary['total_cost_usd']:.6f}")
    logger.info(f"AI评分均值: {summary['ai_score_stats']['mean']:.2f}")
    logger.info(f"AI评分 vs 实际收益相关性: {summary['correlation']['ai_score_vs_return']:.3f}")
    logger.info("=" * 70)
    logger.info("✅ Phase 9A AI探针分析完成")


if __name__ == '__main__':
    main()
