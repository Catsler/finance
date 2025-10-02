#!/usr/bin/env python3
"""
Phase 6E准备工具：股票池配置生成

功能:
    - 生成stock_pool.yaml配置文件
    - 支持方案A（保守版）和方案B（激进版）
    - 使用ruamel.yaml保持格式和注释

用法:
    # 方案A（保守版，长江电力替换中芯国际）
    python scripts/generate_stock_pool_yaml.py --plan A

    # 方案B（激进版，保留中芯国际）
    python scripts/generate_stock_pool_yaml.py --plan B
"""

import argparse
from ruamel.yaml import YAML


# 方案定义
PLANS = {
    'A': {
        'name': '保守版（20只纯A股）',
        'description': '使用长江电力替换中芯国际，避免科创板数据问题',
        'new_stocks': [
            ('300059.SZ', '东方财富', '金融', '金融科技'),
            ('601012.SH', '隆基绿能', '新能源', '光伏'),
            ('603288.SH', '海天味业', '消费', '调味品'),
            ('000333.SZ', '美的集团', '消费', '家电'),
            ('002475.SZ', '立讯精密', '科技', '电子制造'),
            ('600309.SH', '万华化学', '周期', '化工'),
            ('600031.SH', '三一重工', '周期', '机械'),
            ('300760.SZ', '迈瑞医疗', '医药', '医疗器械'),
            ('600900.SH', '长江电力', '公用事业', '电力'),  # 替换中芯国际
            ('002920.SZ', '德赛西威', '科技', '汽车电子'),
        ]
    },
    'B': {
        'name': '激进版（20只含科创板）',
        'description': '保留中芯国际，但需确保数据完整性',
        'new_stocks': [
            ('300059.SZ', '东方财富', '金融', '金融科技'),
            ('601012.SH', '隆基绿能', '新能源', '光伏'),
            ('603288.SH', '海天味业', '消费', '调味品'),
            ('000333.SZ', '美的集团', '消费', '家电'),
            ('002475.SZ', '立讯精密', '科技', '电子制造'),
            ('600309.SH', '万华化学', '周期', '化工'),
            ('600031.SH', '三一重工', '周期', '机械'),
            ('300760.SZ', '迈瑞医疗', '医药', '医疗器械'),
            ('688981.SH', '中芯国际', '科技', '半导体'),  # 科创板
            ('002920.SZ', '德赛西威', '科技', '汽车电子'),
        ]
    }
}


def generate_config(plan='A'):
    """
    生成股票池配置

    Args:
        plan: 'A' (保守), 'B' (激进)

    Returns:
        dict: 配置字典
        str: 方案名称
    """
    config = {}

    # Small cap (Phase 0-6C的10只)
    config['stock_pools'] = {}
    config['stock_pools']['small_cap'] = [
        {'symbol': '000001.SZ', 'name': '平安银行', 'industry': '金融', 'sector': '银行'},
        {'symbol': '601318.SH', 'name': '中国平安', 'industry': '金融', 'sector': '保险'},
        {'symbol': '000858.SZ', 'name': '五粮液', 'industry': '消费', 'sector': '白酒'},
        {'symbol': '600519.SH', 'name': '贵州茅台', 'industry': '消费', 'sector': '白酒'},
        {'symbol': '300750.SZ', 'name': '宁德时代', 'industry': '新能源', 'sector': '电池'},
        {'symbol': '600036.SH', 'name': '招商银行', 'industry': '金融', 'sector': '银行'},
        {'symbol': '002594.SZ', 'name': '比亚迪', 'industry': '新能源', 'sector': '汽车'},
        {'symbol': '000002.SZ', 'name': '万科A', 'industry': '地产', 'sector': '房地产'},
        {'symbol': '600276.SH', 'name': '恒瑞医药', 'industry': '医药', 'sector': '化学制药'},
        {'symbol': '601166.SH', 'name': '兴业银行', 'industry': '金融', 'sector': '银行'},
    ]

    # Medium cap (Phase 6E扩展到20只)
    plan_config = PLANS[plan]
    config['stock_pools']['medium_cap'] = {
        'inherit_from': 'small_cap',
        'plan': plan,
        'plan_name': plan_config['name'],
        'plan_description': plan_config['description'],
        'additional': [
            {'symbol': s[0], 'name': s[1], 'industry': s[2], 'sector': s[3]}
            for s in plan_config['new_stocks']
        ]
    }

    # Industry config
    config['industry_config'] = {
        '金融': ['银行', '保险', '金融科技'],
        '消费': ['白酒', '调味品', '家电'],
        '新能源': ['电池', '汽车', '光伏'],
        '科技': ['电子制造', '汽车电子', '半导体'],
        '医药': ['化学制药', '医疗器械'],
        '周期': ['化工', '机械'],
        '地产': ['房地产'],
        '公用事业': ['电力']
    }

    # Metadata
    config['_metadata'] = {
        'version': '1.0.0',
        'phase': 'Phase 6E',
        'created_by': 'generate_stock_pool_yaml.py',
        'warning': '请勿手动编辑此文件，修改请重新运行生成脚本'
    }

    return config, plan_config['name']


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='生成股票池配置')
    parser.add_argument('--plan', choices=['A', 'B'], default='A',
                        help='方案选择: A=保守, B=激进 (默认A)')
    args = parser.parse_args()

    config, plan_name = generate_config(args.plan)

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    yaml.width = 4096

    output_file = 'stock_pool.yaml'
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f)

    print(f"\n{'='*60}")
    print(f"✓ {output_file} 已生成")
    print(f"{'='*60}")
    print(f"  方案: {args.plan} - {plan_name}")
    print(f"  Stock pools: {len(config['stock_pools'])}")
    print(f"  - small_cap: {len(config['stock_pools']['small_cap'])}只")

    total_medium = len(config['stock_pools']['small_cap']) + \
                   len(config['stock_pools']['medium_cap']['additional'])
    print(f"  - medium_cap: {total_medium}只 (继承{len(config['stock_pools']['small_cap'])}只 + 新增{len(config['stock_pools']['medium_cap']['additional'])}只)")

    print(f"\n行业分布:")
    for industry, sectors in config['industry_config'].items():
        print(f"  {industry}: {', '.join(sectors)}")

    print(f"\n⚠️  {config['_metadata']['warning']}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
