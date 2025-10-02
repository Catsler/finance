# Phase 0 环境配置指南

本文档用于配置 Stock 量化交易系统的开发环境。

## 📋 系统要求

- **操作系统**: macOS / Linux / Windows
- **Python 版本**: 3.8 - 3.10（推荐 3.9）

> ⚠️ **注意**: Qlib 对 Python 3.11+ 的支持可能不完整，建议使用 3.8-3.10

## 🔧 依赖安装

### 方式1：一键安装（推荐）

```bash
# 安装核心依赖
pip install "akshare>=1.12.0"
pip install "pandas>=1.3.0"
pip install "qlib[all]>=0.9.0"
```

> 💡 `qlib[all]` 会自动安装常用依赖（matplotlib、numpy 等）

### 方式2：分步安装

```bash
# 基础依赖
pip install "pandas>=1.3.0"
pip install "numpy>=1.20.0"

# 数据源
pip install "akshare>=1.12.0"

# Qlib 核心
pip install "qlib>=0.9.0"

# 可视化（可选）
pip install matplotlib seaborn
```

## ✅ 安装自检

复制以下代码到终端运行：

```python
# 检查 Python 版本
import sys
print(f"Python 版本: {sys.version}")

# 检查核心依赖
import akshare as ak
import pandas as pd
import qlib

print(f"AKShare 版本: {ak.__version__}")
print(f"Pandas 版本: {pd.__version__}")
print(f"Qlib 版本: {qlib.__version__}")

print("\n✅ 所有依赖安装成功！")
```

**预期输出**：
```
Python 版本: 3.9.x ...
AKShare 版本: 1.12.x
Pandas 版本: 1.3.x
Qlib 版本: 0.9.x

✅ 所有依赖安装成功！
```

## 🔍 常见问题

### 问题1：Qlib 安装失败

**症状**：
```bash
ERROR: Failed building wheel for qlib
```

**解决方案**：
```bash
# 先升级基础工具
pip install --upgrade pip setuptools wheel

# 再尝试安装 Qlib
pip install qlib
```

**参考资源**：
- [Qlib 官方安装文档](https://qlib.readthedocs.io/en/latest/start/installation.html)

---

### 问题2：缺少 TA-Lib

**症状**：
```
ImportError: No module named 'talib'
```

**解决方案**：

#### macOS
```bash
# 使用 Homebrew
brew install ta-lib

# 然后安装 Python 包装器
pip install TA-Lib
```

#### Linux (Ubuntu/Debian)
```bash
# 安装依赖
sudo apt-get install build-essential

# 从源码编译 TA-Lib
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install

# 安装 Python 包装器
pip install TA-Lib
```

#### Windows
```bash
# 下载预编译的 wheel 文件
# 访问：https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
# 选择对应 Python 版本的 .whl 文件

# 安装
pip install TA_Lib‑0.4.xx‑cpxx‑cpxxm‑win_amd64.whl
```

---

### 问题3：AKShare 首次调用很慢

**症状**：
```python
import akshare as ak
df = ak.stock_zh_a_hist("000001")  # 等待很久
```

**原因**：
- AKShare 首次运行需要下载缓存数据
- 网络速度影响较大

**解决方案**：
- 耐心等待第一次执行完成
- 后续调用会快很多
- 如果超过 5 分钟，检查网络连接

---

### 问题4：Qlib 初始化错误

**症状**：
```python
import qlib
qlib.init()  # 报错
```

**解决方案**：
```python
import qlib

# 明确指定数据路径
qlib.init(
    provider_uri="~/.qlib/qlib_data/cn_data",
    region="cn"
)
```

---

### 问题5：网络代理问题

**症状**：
- AKShare 无法获取数据
- pip 安装超时

**解决方案**：

```bash
# 方法1：配置 pip 镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple akshare

# 方法2：设置代理（如果使用 VPN）
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
```

---

## 📦 可选依赖

### 数据可视化
```bash
pip install matplotlib seaborn plotly
```

### Jupyter Notebook（推荐用于策略实验）
```bash
pip install jupyter notebook
jupyter notebook  # 启动
```

### 代码质量工具
```bash
pip install black flake8 mypy
```

---

## 🧪 完整测试脚本

保存为 `test_environment.py` 并运行：

```python
#!/usr/bin/env python3
"""环境完整性测试脚本"""

import sys

def check_python_version():
    """检查 Python 版本"""
    version = sys.version_info
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")

    if not (3, 8) <= (version.major, version.minor) <= (3, 10):
        print("⚠️  警告: 推荐使用 Python 3.8-3.10")

def check_dependencies():
    """检查依赖包"""
    required = {
        "akshare": "1.12.0",
        "pandas": "1.3.0",
        "qlib": "0.9.0",
    }

    for package, min_version in required.items():
        try:
            module = __import__(package)
            version = getattr(module, "__version__", "未知")
            print(f"✓ {package:15s} {version}")
        except ImportError:
            print(f"✗ {package:15s} 未安装")
            return False
    return True

def test_akshare():
    """测试 AKShare 可用性"""
    try:
        import akshare as ak
        # 简单测试（不实际下载数据）
        print("✓ AKShare 可用")
        return True
    except Exception as e:
        print(f"✗ AKShare 测试失败: {e}")
        return False

def test_qlib():
    """测试 Qlib 可用性"""
    try:
        import qlib
        # 不初始化，只检查导入
        print("✓ Qlib 可用")
        return True
    except Exception as e:
        print(f"✗ Qlib 测试失败: {e}")
        return False

def main():
    print("=" * 50)
    print("Stock 量化系统 - 环境检查")
    print("=" * 50)

    check_python_version()

    print("\n依赖检查：")
    deps_ok = check_dependencies()

    print("\n功能测试：")
    akshare_ok = test_akshare()
    qlib_ok = test_qlib()

    print("\n" + "=" * 50)
    if deps_ok and akshare_ok and qlib_ok:
        print("✅ 环境配置完成，可以开始 Phase 0！")
    else:
        print("❌ 环境配置不完整，请检查上述错误")
    print("=" * 50)

if __name__ == "__main__":
    main()
```

运行测试：
```bash
python test_environment.py
```

---

## 📚 参考资源

- [Qlib 官方文档](https://qlib.readthedocs.io/)
- [AKShare 文档](https://akshare.akfamily.xyz/)
- [Pandas 文档](https://pandas.pydata.org/docs/)
- [Python 虚拟环境指南](https://docs.python.org/3/tutorial/venv.html)

---

## 💡 虚拟环境推荐

建议使用虚拟环境隔离项目依赖：

```bash
# 创建虚拟环境
python -m venv stock_env

# 激活虚拟环境
# macOS/Linux:
source stock_env/bin/activate

# Windows:
stock_env\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 退出虚拟环境
deactivate
```

---

**最后更新**: 2025-10-01
**维护者**: Agent 1 (文档专家)