# Phase 8 数据质量检查记录

## Phase 8.1: 二十年老股票池验证

**执行时间**: 2025-10-05
**目标**: 验证五只白马股 2005-2024 数据完整性

---

### Step 1: 批量下载

**命令**: `python scripts/batch_download.py --years 20`
**执行时间**: 2025-10-05 18:31-18:33

**输出**:
```text
✅ 加载 medium_cap（20 只股票）

🚀 开始批量下载 20 只股票的 20 年数据...


[1/20] 000001.SZ - 平安银行 (银行)

============================================================
正在下载: 000001.SZ
============================================================
❌ 000001.SZ 下载失败
错误: /Users/elie/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
2025-10-05 18:31:26,398 [INFO] ============================================================
2025-10-05 18:31:26,402 [INFO] Stock 数据转换工具 - Phase 0
2025-10-05 18:31:26,402 [INFO] ============================================================
2025-10-05 18:31:26,406 [INFO] 正在获取 000001.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:31:26,411 [WARNING] 第 1 次尝试失败，1 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.000001&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x1137c1070>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:27,417 [INFO] 正在获取 000001.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:31:27,426 [WARNING] 第 2 次尝试失败，2 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.000001&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x11379af10>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:29,429 [INFO] 正在获取 000001.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:31:29,434 [ERROR] 所有重试失败: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.000001&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x1137c1040>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:29,436 [ERROR] ============================================================
2025-10-05 18:31:29,436 [ERROR] ❌ Validation Failed: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.000001&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x1137c1040>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:29,437 [ERROR] ============================================================


[2/20] 601318.SH - 中国平安 (保险)

============================================================
正在下载: 601318.SH
============================================================
❌ 601318.SH 下载失败
错误: /Users/elie/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
2025-10-05 18:31:31,921 [INFO] ============================================================
2025-10-05 18:31:31,922 [INFO] Stock 数据转换工具 - Phase 0
2025-10-05 18:31:31,922 [INFO] ============================================================
2025-10-05 18:31:31,923 [INFO] 正在获取 601318.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:31:31,924 [WARNING] 第 1 次尝试失败，1 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.601318&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x10fe1dc10>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:32,929 [INFO] 正在获取 601318.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:31:32,940 [WARNING] 第 2 次尝试失败，2 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.601318&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x10fe1dc10>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:34,946 [INFO] 正在获取 601318.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:31:34,951 [ERROR] 所有重试失败: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.601318&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x10fe481c0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:34,952 [ERROR] ============================================================
2025-10-05 18:31:34,953 [ERROR] ❌ Validation Failed: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.601318&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x10fe481c0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:34,954 [ERROR] ============================================================


[3/20] 000858.SZ - 五粮液 (白酒)

============================================================
正在下载: 000858.SZ
============================================================
❌ 000858.SZ 下载失败
错误: /Users/elie/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
2025-10-05 18:31:37,430 [INFO] ============================================================
2025-10-05 18:31:37,431 [INFO] Stock 数据转换工具 - Phase 0
2025-10-05 18:31:37,431 [INFO] ============================================================
2025-10-05 18:31:37,432 [INFO] 正在获取 000858.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:31:37,433 [WARNING] 第 1 次尝试失败，1 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.000858&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x1137ae490>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:38,439 [INFO] 正在获取 000858.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:31:38,449 [WARNING] 第 2 次尝试失败，2 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.000858&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x1136847f0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:40,454 [INFO] 正在获取 000858.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:31:40,459 [ERROR] 所有重试失败: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.000858&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x1137ae400>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:40,461 [ERROR] ============================================================
2025-10-05 18:31:40,461 [ERROR] ❌ Validation Failed: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.000858&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x1137ae400>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:40,462 [ERROR] ============================================================


[4/20] 600519.SH - 贵州茅台 (白酒)

============================================================
正在下载: 600519.SH
============================================================
❌ 600519.SH 下载失败
错误: /Users/elie/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
2025-10-05 18:31:42,945 [INFO] ============================================================
2025-10-05 18:31:42,946 [INFO] Stock 数据转换工具 - Phase 0
2025-10-05 18:31:42,946 [INFO] ============================================================
2025-10-05 18:31:42,947 [INFO] 正在获取 600519.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:31:42,948 [WARNING] 第 1 次尝试失败，1 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600519&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x11029be50>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:43,954 [INFO] 正在获取 600519.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:31:43,963 [WARNING] 第 2 次尝试失败，2 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600519&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x11029bac0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:45,969 [INFO] 正在获取 600519.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:31:45,975 [ERROR] 所有重试失败: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600519&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x1102c7400>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:45,976 [ERROR] ============================================================
2025-10-05 18:31:45,977 [ERROR] ❌ Validation Failed: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600519&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x1102c7400>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:45,978 [ERROR] ============================================================


[5/20] 300750.SZ - 宁德时代 (电池)

============================================================
正在下载: 300750.SZ
============================================================
❌ 300750.SZ 下载失败
错误: /Users/elie/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
2025-10-05 18:31:48,507 [INFO] ============================================================
2025-10-05 18:31:48,509 [INFO] Stock 数据转换工具 - Phase 0
2025-10-05 18:31:48,509 [INFO] ============================================================
2025-10-05 18:31:48,509 [INFO] 正在获取 300750.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:31:48,511 [WARNING] 第 1 次尝试失败，1 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.300750&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x111e1bf10>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:49,517 [INFO] 正在获取 300750.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:31:49,526 [WARNING] 第 2 次尝试失败，2 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.300750&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x111e1bb80>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:51,533 [INFO] 正在获取 300750.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:31:51,539 [ERROR] 所有重试失败: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.300750&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x111e45070>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:51,540 [ERROR] ============================================================
2025-10-05 18:31:51,541 [ERROR] ❌ Validation Failed: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.300750&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x111e45070>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:51,541 [ERROR] ============================================================


[6/20] 600036.SH - 招商银行 (银行)

============================================================
正在下载: 600036.SH
============================================================
❌ 600036.SH 下载失败
错误: /Users/elie/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
2025-10-05 18:31:54,042 [INFO] ============================================================
2025-10-05 18:31:54,043 [INFO] Stock 数据转换工具 - Phase 0
2025-10-05 18:31:54,044 [INFO] ============================================================
2025-10-05 18:31:54,044 [INFO] 正在获取 600036.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:31:54,046 [WARNING] 第 1 次尝试失败，1 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600036&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x1141be430>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:55,052 [INFO] 正在获取 600036.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:31:55,061 [WARNING] 第 2 次尝试失败，2 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600036&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x114094790>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:57,067 [INFO] 正在获取 600036.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:31:57,073 [ERROR] 所有重试失败: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600036&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x1141be2b0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:57,074 [ERROR] ============================================================
2025-10-05 18:31:57,075 [ERROR] ❌ Validation Failed: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600036&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x1141be2b0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:31:57,075 [ERROR] ============================================================


[7/20] 002594.SZ - 比亚迪 (汽车)

============================================================
正在下载: 002594.SZ
============================================================
❌ 002594.SZ 下载失败
错误: /Users/elie/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
2025-10-05 18:31:59,548 [INFO] ============================================================
2025-10-05 18:31:59,549 [INFO] Stock 数据转换工具 - Phase 0
2025-10-05 18:31:59,549 [INFO] ============================================================
2025-10-05 18:31:59,550 [INFO] 正在获取 002594.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:31:59,551 [WARNING] 第 1 次尝试失败，1 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.002594&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x111a5dd90>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:00,557 [INFO] 正在获取 002594.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:32:00,567 [WARNING] 第 2 次尝试失败，2 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.002594&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x111a5da00>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:02,571 [INFO] 正在获取 002594.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:32:02,578 [ERROR] 所有重试失败: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.002594&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x111a88340>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:02,579 [ERROR] ============================================================
2025-10-05 18:32:02,580 [ERROR] ❌ Validation Failed: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.002594&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x111a88340>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:02,581 [ERROR] ============================================================


[8/20] 000002.SZ - 万科A (房地产)

============================================================
正在下载: 000002.SZ
============================================================
❌ 000002.SZ 下载失败
错误: /Users/elie/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
2025-10-05 18:32:05,067 [INFO] ============================================================
2025-10-05 18:32:05,067 [INFO] Stock 数据转换工具 - Phase 0
2025-10-05 18:32:05,068 [INFO] ============================================================
2025-10-05 18:32:05,068 [INFO] 正在获取 000002.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:32:05,070 [WARNING] 第 1 次尝试失败，1 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.000002&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x1138fcee0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:06,075 [INFO] 正在获取 000002.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:32:06,085 [WARNING] 第 2 次尝试失败，2 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.000002&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x1138fcb50>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:08,091 [INFO] 正在获取 000002.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:32:08,097 [ERROR] 所有重试失败: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.000002&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x113925040>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:08,098 [ERROR] ============================================================
2025-10-05 18:32:08,099 [ERROR] ❌ Validation Failed: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.000002&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x113925040>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:08,100 [ERROR] ============================================================


[9/20] 600276.SH - 恒瑞医药 (化学制药)

============================================================
正在下载: 600276.SH
============================================================
❌ 600276.SH 下载失败
错误: /Users/elie/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
2025-10-05 18:32:10,584 [INFO] ============================================================
2025-10-05 18:32:10,584 [INFO] Stock 数据转换工具 - Phase 0
2025-10-05 18:32:10,585 [INFO] ============================================================
2025-10-05 18:32:10,585 [INFO] 正在获取 600276.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:32:10,587 [WARNING] 第 1 次尝试失败，1 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600276&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x11365dcd0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:11,592 [INFO] 正在获取 600276.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:32:11,603 [WARNING] 第 2 次尝试失败，2 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600276&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x11365dcd0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:13,609 [INFO] 正在获取 600276.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:32:13,614 [ERROR] 所有重试失败: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600276&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x113688280>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:13,615 [ERROR] ============================================================
2025-10-05 18:32:13,616 [ERROR] ❌ Validation Failed: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600276&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x113688280>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:13,617 [ERROR] ============================================================


[10/20] 601166.SH - 兴业银行 (银行)

============================================================
正在下载: 601166.SH
============================================================
❌ 601166.SH 下载失败
错误: /Users/elie/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
2025-10-05 18:32:16,088 [INFO] ============================================================
2025-10-05 18:32:16,088 [INFO] Stock 数据转换工具 - Phase 0
2025-10-05 18:32:16,088 [INFO] ============================================================
2025-10-05 18:32:16,089 [INFO] 正在获取 601166.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:32:16,091 [WARNING] 第 1 次尝试失败，1 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.601166&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x11191ca90>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:17,096 [INFO] 正在获取 601166.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:32:17,108 [WARNING] 第 2 次尝试失败，2 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.601166&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x11191c970>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:19,113 [INFO] 正在获取 601166.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:32:19,116 [ERROR] 所有重试失败: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.601166&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x111946040>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:19,117 [ERROR] ============================================================
2025-10-05 18:32:19,117 [ERROR] ❌ Validation Failed: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.601166&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x111946040>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:19,118 [ERROR] ============================================================


[11/20] 300059.SZ - 东方财富 (金融科技)

============================================================
正在下载: 300059.SZ
============================================================
❌ 300059.SZ 下载失败
错误: /Users/elie/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
2025-10-05 18:32:21,583 [INFO] ============================================================
2025-10-05 18:32:21,584 [INFO] Stock 数据转换工具 - Phase 0
2025-10-05 18:32:21,584 [INFO] ============================================================
2025-10-05 18:32:21,585 [INFO] 正在获取 300059.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:32:21,586 [WARNING] 第 1 次尝试失败，1 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.300059&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x1116618b0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:22,592 [INFO] 正在获取 300059.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:32:22,603 [WARNING] 第 2 次尝试失败，2 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.300059&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x10323dee0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:24,604 [INFO] 正在获取 300059.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:32:24,610 [ERROR] 所有重试失败: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.300059&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x11153d9d0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:24,611 [ERROR] ============================================================
2025-10-05 18:32:24,611 [ERROR] ❌ Validation Failed: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.300059&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x11153d9d0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:24,612 [ERROR] ============================================================


[12/20] 601012.SH - 隆基绿能 (光伏)

============================================================
正在下载: 601012.SH
============================================================
❌ 601012.SH 下载失败
错误: /Users/elie/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
2025-10-05 18:32:27,084 [INFO] ============================================================
2025-10-05 18:32:27,085 [INFO] Stock 数据转换工具 - Phase 0
2025-10-05 18:32:27,085 [INFO] ============================================================
2025-10-05 18:32:27,086 [INFO] 正在获取 601012.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:32:27,087 [WARNING] 第 1 次尝试失败，1 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.601012&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x11039dca0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:28,093 [INFO] 正在获取 601012.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:32:28,102 [WARNING] 第 2 次尝试失败，2 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.601012&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x11039dca0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:30,105 [INFO] 正在获取 601012.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:32:30,111 [ERROR] 所有重试失败: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.601012&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x1103c8250>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:30,112 [ERROR] ============================================================
2025-10-05 18:32:30,113 [ERROR] ❌ Validation Failed: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.601012&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x1103c8250>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:30,113 [ERROR] ============================================================


[13/20] 603288.SH - 海天味业 (调味品)

============================================================
正在下载: 603288.SH
============================================================
❌ 603288.SH 下载失败
错误: /Users/elie/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
2025-10-05 18:32:32,589 [INFO] ============================================================
2025-10-05 18:32:32,589 [INFO] Stock 数据转换工具 - Phase 0
2025-10-05 18:32:32,590 [INFO] ============================================================
2025-10-05 18:32:32,590 [INFO] 正在获取 603288.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:32:32,592 [WARNING] 第 1 次尝试失败，1 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.603288&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x111919cd0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:33,597 [INFO] 正在获取 603288.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:32:33,607 [WARNING] 第 2 次尝试失败，2 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.603288&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x111919cd0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:35,613 [INFO] 正在获取 603288.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:32:35,620 [ERROR] 所有重试失败: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.603288&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x111944280>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:35,621 [ERROR] ============================================================
2025-10-05 18:32:35,622 [ERROR] ❌ Validation Failed: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.603288&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x111944280>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:35,623 [ERROR] ============================================================


[14/20] 000333.SZ - 美的集团 (家电)

============================================================
正在下载: 000333.SZ
============================================================
❌ 000333.SZ 下载失败
错误: /Users/elie/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
2025-10-05 18:32:38,093 [INFO] ============================================================
2025-10-05 18:32:38,093 [INFO] Stock 数据转换工具 - Phase 0
2025-10-05 18:32:38,093 [INFO] ============================================================
2025-10-05 18:32:38,094 [INFO] 正在获取 000333.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:32:38,096 [WARNING] 第 1 次尝试失败，1 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.000333&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x11239dc40>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:39,101 [INFO] 正在获取 000333.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:32:39,111 [WARNING] 第 2 次尝试失败，2 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.000333&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x11239dc40>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:41,118 [INFO] 正在获取 000333.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:32:41,123 [ERROR] 所有重试失败: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.000333&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x1123c81f0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:41,124 [ERROR] ============================================================
2025-10-05 18:32:41,125 [ERROR] ❌ Validation Failed: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.000333&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x1123c81f0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:41,126 [ERROR] ============================================================


[15/20] 002475.SZ - 立讯精密 (电子制造)

============================================================
正在下载: 002475.SZ
============================================================
❌ 002475.SZ 下载失败
错误: /Users/elie/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
2025-10-05 18:32:43,596 [INFO] ============================================================
2025-10-05 18:32:43,596 [INFO] Stock 数据转换工具 - Phase 0
2025-10-05 18:32:43,597 [INFO] ============================================================
2025-10-05 18:32:43,597 [INFO] 正在获取 002475.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:32:43,599 [WARNING] 第 1 次尝试失败，1 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.002475&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x112073160>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:44,604 [INFO] 正在获取 002475.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:32:44,613 [WARNING] 第 2 次尝试失败，2 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.002475&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x11205adf0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:46,620 [INFO] 正在获取 002475.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:32:46,624 [ERROR] 所有重试失败: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.002475&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x112073130>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:46,624 [ERROR] ============================================================
2025-10-05 18:32:46,625 [ERROR] ❌ Validation Failed: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.002475&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x112073130>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:46,626 [ERROR] ============================================================


[16/20] 600309.SH - 万华化学 (化工)

============================================================
正在下载: 600309.SH
============================================================
❌ 600309.SH 下载失败
错误: /Users/elie/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
2025-10-05 18:32:49,183 [INFO] ============================================================
2025-10-05 18:32:49,184 [INFO] Stock 数据转换工具 - Phase 0
2025-10-05 18:32:49,185 [INFO] ============================================================
2025-10-05 18:32:49,185 [INFO] 正在获取 600309.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:32:49,187 [WARNING] 第 1 次尝试失败，1 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600309&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x110340070>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:50,192 [INFO] 正在获取 600309.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:32:50,202 [WARNING] 第 2 次尝试失败，2 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600309&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x11031af10>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:52,208 [INFO] 正在获取 600309.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:32:52,214 [ERROR] 所有重试失败: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600309&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x110340040>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:52,216 [ERROR] ============================================================
2025-10-05 18:32:52,217 [ERROR] ❌ Validation Failed: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600309&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x110340040>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:52,218 [ERROR] ============================================================


[17/20] 600031.SH - 三一重工 (机械)

============================================================
正在下载: 600031.SH
============================================================
❌ 600031.SH 下载失败
错误: /Users/elie/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
2025-10-05 18:32:54,713 [INFO] ============================================================
2025-10-05 18:32:54,713 [INFO] Stock 数据转换工具 - Phase 0
2025-10-05 18:32:54,713 [INFO] ============================================================
2025-10-05 18:32:54,714 [INFO] 正在获取 600031.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:32:54,715 [WARNING] 第 1 次尝试失败，1 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600031&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x10fddce50>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:55,721 [INFO] 正在获取 600031.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:32:55,731 [WARNING] 第 2 次尝试失败，2 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600031&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x10fddcac0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:57,736 [INFO] 正在获取 600031.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:32:57,741 [ERROR] 所有重试失败: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600031&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x10fe07400>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:57,742 [ERROR] ============================================================
2025-10-05 18:32:57,743 [ERROR] ❌ Validation Failed: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600031&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x10fe07400>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:32:57,744 [ERROR] ============================================================


[18/20] 300760.SZ - 迈瑞医疗 (医疗器械)

============================================================
正在下载: 300760.SZ
============================================================
❌ 300760.SZ 下载失败
错误: /Users/elie/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
2025-10-05 18:33:00,242 [INFO] ============================================================
2025-10-05 18:33:00,243 [INFO] Stock 数据转换工具 - Phase 0
2025-10-05 18:33:00,243 [INFO] ============================================================
2025-10-05 18:33:00,243 [INFO] 正在获取 300760.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:33:00,245 [WARNING] 第 1 次尝试失败，1 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.300760&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x11439bfa0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:33:01,251 [INFO] 正在获取 300760.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:33:01,261 [WARNING] 第 2 次尝试失败，2 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.300760&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x11439bc10>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:33:03,265 [INFO] 正在获取 300760.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:33:03,272 [ERROR] 所有重试失败: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.300760&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x1143c50a0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:33:03,273 [ERROR] ============================================================
2025-10-05 18:33:03,274 [ERROR] ❌ Validation Failed: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.300760&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x1143c50a0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:33:03,275 [ERROR] ============================================================


[19/20] 600900.SH - 长江电力 (电力)

============================================================
正在下载: 600900.SH
============================================================
❌ 600900.SH 下载失败
错误: /Users/elie/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
2025-10-05 18:33:05,721 [INFO] ============================================================
2025-10-05 18:33:05,721 [INFO] Stock 数据转换工具 - Phase 0
2025-10-05 18:33:05,722 [INFO] ============================================================
2025-10-05 18:33:05,722 [INFO] 正在获取 600900.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:33:05,724 [WARNING] 第 1 次尝试失败，1 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600900&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x11035dbb0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:33:06,727 [INFO] 正在获取 600900.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:33:06,736 [WARNING] 第 2 次尝试失败，2 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600900&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x11035da90>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:33:08,738 [INFO] 正在获取 600900.SH 数据（20051005 ~ 20251005）...
2025-10-05 18:33:08,744 [ERROR] 所有重试失败: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600900&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x110388160>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:33:08,745 [ERROR] ============================================================
2025-10-05 18:33:08,746 [ERROR] ❌ Validation Failed: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=1.600900&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x110388160>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:33:08,746 [ERROR] ============================================================


[20/20] 002920.SZ - 德赛西威 (汽车电子)

============================================================
正在下载: 002920.SZ
============================================================
❌ 002920.SZ 下载失败
错误: /Users/elie/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
2025-10-05 18:33:11,202 [INFO] ============================================================
2025-10-05 18:33:11,202 [INFO] Stock 数据转换工具 - Phase 0
2025-10-05 18:33:11,202 [INFO] ============================================================
2025-10-05 18:33:11,203 [INFO] 正在获取 002920.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:33:11,205 [WARNING] 第 1 次尝试失败，1 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.002920&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x10fd1af40>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:33:12,210 [INFO] 正在获取 002920.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:33:12,219 [WARNING] 第 2 次尝试失败，2 秒后重试: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.002920&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x10fd1abb0>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:33:14,221 [INFO] 正在获取 002920.SZ 数据（20051005 ~ 20251005）...
2025-10-05 18:33:14,226 [ERROR] 所有重试失败: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.002920&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x10fd44040>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:33:14,228 [ERROR] ============================================================
2025-10-05 18:33:14,228 [ERROR] ❌ Validation Failed: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf116&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=2&secid=0.002920&beg=20051005&end=20251005 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x10fd44040>: Failed to resolve 'push2his.eastmoney.com' ([Errno 8] nodename nor servname provided, or not known)"))
2025-10-05 18:33:14,229 [ERROR] ============================================================


============================================================
📊 下载报告已生成: batch_download_report.md
============================================================
成功: 0/20  |  失败: 20/20  |  总耗时: 70.4s
============================================================
```

---

### Step 2: 数据质量检查

**命令**: `python scripts/check_stock_data.py --auto-fallback`
**执行时间**: 2025-10-05 18:33-18:34

**完整输出**（逐字粘贴）:
```text
================================================================================
股票池扩展数据可用性检查
================================================================================
总计: 10只  |  问题: 0只  |  替换: 1只  |  警告: 0只  |  正常: 9只
================================================================================

[REPLACED]
  688981.SH    中芯国际         文件不存在                                    → 自动替换为 600900.SH (长江电力)

[OK]
  000333.SZ    美的集团         727条数据，充足                                → 无需替换
  002475.SZ    立讯精密         727条数据，充足                                → 无需替换
  002920.SZ    德赛西威         727条数据，充足                                → 无需替换
  300059.SZ    东方财富         727条数据，充足                                → 无需替换
  300760.SZ    迈瑞医疗         727条数据，充足                                → 无需替换
  600031.SH    三一重工         727条数据，充足                                → 无需替换
  600309.SH    万华化学         727条数据，充足                                → 无需替换
  601012.SH    隆基绿能         727条数据，充足                                → 无需替换
  603288.SH    海天味业         727条数据，充足                                → 无需替换
================================================================================

================================================================================
自动替换执行:
  688981.SH → 600900.SH (中芯国际数据不足（科创板）)
================================================================================

最终股票列表已更新，共10只
✓ 已保存: results/phase6e_final_symbols.json
```

**关键数据**（手工提取）:
- 整体覆盖率: 0%（20/20 下载失败，等待网络/SSL问题修复后重试）
- 最短公共区间: 待批量下载成功后确认
- 缺失情况: 全部目标股票 2005-2024（NameResolutionError: push2his.eastmoney.com）

---

### Go/No-Go 决策

| 覆盖率 | 年化收益 | 结论 | 下一步动作 | ✓ |
|--------|----------|------|-----------|---|
| <70% | - | ❌ 数据不足 | 终止，填写复盘 | [x] |
| 70-80% | - | 🟡 应急方案 | 改测 2010-2024 | [ ] |
| ≥80% | ≥12% | ✅ 优秀 | 考虑主推策略 | [ ] |
| ≥80% | 8-12% | 🟢 合格 | 作为备选方案 | [ ] |
| ≥80% | <8% | ❌ 不达标 | 复盘+冷静期 | [ ] |

**实际结果**:
- 覆盖率: 0%
- 年化收益: 待 Step 3
- **决策**: ❌ 数据不足（首行勾选）

---

### 应急方案（场景：覆盖率 70-80%）

**调整参数**:
- 测试区间: 2005-2024 → **2010-2024**
- 年化预期: ≥8% → **≥10%**

**修改后的 Step 3 命令**:
```bash
python scripts/phase6d_backtest.py \
  --pool legacy_stars \
  --start-year 2010 \
  --end-year 2024 \
  --full
```

---

### Step 3: 回测结果（≥70% 覆盖率后执行）

快速对比

Phase 8.1:
- 年化收益: ?%
- 最大回撤: -?%
- 换手率: ?%

基准对比:
- 沪深300: 年化 ?% → 超额 ±?%
- 中证500: 年化 ?% → 超额 ±?%

一句话结论: [Phase 8.1 跑赢/跑输 XX 个百分点]

关键年份表现（熊市检验）

| 年份   | Phase 8.1 | 沪深300  | 备注   |
|------|-----------|--------|------|
| 2008 | ?%        | -65.4% | 金融危机 |
| 2015 | ?%        | +5.6%  | 股灾   |
| 2018 | ?%        | -25.3% | 贸易战  |

---

### 复盘记录（年化 <8% 时填写）

根因假设

- 动量策略不适合白马股
- 月度调仓过于频繁
- MA5/MA10 不适配老股票波动特征

冷静期约束

失败日期: 2025-01-XX
最早调参日期: 2025-01-YY（+7天）

冷静期任务:
- 回顾 Phase 6E 的 2023 复盘
- 列出 Phase 6E 可优化点（≥3 条）
- 评估调参 vs 优化 Phase 6E 的投入产出比

冷静期后决策: [日期后填写]
- Archive Phase 8.1，不调参
- 尝试季度调仓（Phase 8.2-opt）
- 优化 Phase 6E（止损/行业轮动）

---

### 备注

- 不在当前轮调参：失败后先冷静期，再评估
- 基准数据来源：手工查询或从已有 benchmark_hs300.csv 提取
- Git 提交时机: Step 1/2 完成后提交，Step 3 完成后再提交
