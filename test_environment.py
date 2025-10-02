#!/usr/bin/env python3
"""
Stock 量化系统 - 环境完整性测试脚本

用法：
    python test_environment.py

功能：
    - 检查 Python 版本
    - 检查核心依赖包
    - 测试 AKShare 可用性
    - 测试 Qlib 可用性
    - 检查项目文件完整性
"""

import sys
from pathlib import Path


def check_python_version():
    """检查 Python 版本"""
    version = sys.version_info
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")

    if not (3, 8) <= (version.major, version.minor) <= (3, 10):
        print("⚠️  警告: 推荐使用 Python 3.8-3.10")
        return False
    return True


def check_dependencies():
    """检查依赖包"""
    required = {
        "akshare": "1.12.0",
        "pandas": "1.3.0",
        "qlib": "0.9.0",
    }

    all_ok = True
    for package, min_version in required.items():
        try:
            module = __import__(package)
            version = getattr(module, "__version__", "未知")
            print(f"✓ {package:15s} {version}")
        except ImportError:
            print(f"✗ {package:15s} 未安装")
            all_ok = False
    return all_ok


def test_akshare():
    """测试 AKShare 可用性"""
    try:
        import akshare as ak

        print("✓ AKShare 可用")
        return True
    except Exception as e:
        print(f"✗ AKShare 测试失败: {e}")
        return False


def test_qlib():
    """测试 Qlib 可用性"""
    try:
        import qlib

        print("✓ Qlib 可用")
        return True
    except Exception as e:
        print(f"✗ Qlib 测试失败: {e}")
        return False


def check_project_files():
    """检查项目文件完整性"""
    project_root = Path(__file__).parent
    required_files = [
        "TODO.md",
        "README.md",
        "config.yaml",
        "docs/phase0-environment-setup.md",
        "docs/phase0-data-validation-checklist.md",
        "docs/phase0-validation-report-template.md",
        "scripts/akshare-to-qlib-converter.py",
    ]

    print("\n项目文件检查：")
    all_ok = True
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            size = full_path.stat().st_size / 1024  # KB
            print(f"✓ {file_path:50s} ({size:.1f} KB)")
        else:
            print(f"✗ {file_path:50s} 缺失")
            all_ok = False
    return all_ok


def main():
    print("=" * 60)
    print("Stock 量化系统 - 环境检查")
    print("=" * 60)

    print("\nPython 版本：")
    python_ok = check_python_version()

    print("\n依赖检查：")
    deps_ok = check_dependencies()

    print("\n功能测试：")
    akshare_ok = test_akshare()
    qlib_ok = test_qlib()

    files_ok = check_project_files()

    print("\n" + "=" * 60)
    if python_ok and deps_ok and akshare_ok and qlib_ok and files_ok:
        print("✅ 环境配置完成，可以开始 Phase 0！")
        print("\n下一步：")
        print("  1. 填写 TODO.md 中的时间节点（T0 = 当前时间）")
        print("  2. 分配任务给 Agent 1-4")
        print("  3. 运行验证脚本：")
        print("     python scripts/akshare-to-qlib-converter.py --symbol 000001.SZ --years 3")
        return 0
    else:
        print("❌ 环境配置不完整，请检查上述错误")
        print("\n解决方案：")
        if not deps_ok:
            print("  - 安装依赖：pip install akshare pandas 'qlib[all]'")
        if not files_ok:
            print("  - 检查项目文件是否完整")
        return 1
    print("=" * 60)


if __name__ == "__main__":
    sys.exit(main())
