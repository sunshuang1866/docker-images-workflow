# 修复摘要

## 修复的问题
修复 `fix_getdeps.py` 中 `_verify_hash` 方法匹配逻辑的 bug：原正则 `r'def _verify_hash\(self\):.*?(?=\n(?:    def |class )|\Z)'` 在 `_verify_hash` 为类中最后一个方法时，`\Z` 会吞噬后续的模块级代码（如 `if __name__ == '__main__':`），导致替换静默失败或文件损坏。

## 修改的文件
- `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/fix_getdeps.py`: 将正则替换改为逐行处理方法，以方法体缩进边界作为终止条件，并增加替换后校验。

## 修复逻辑
对应 CI 分析报告中的**方向 1（置信度: 中）**：

原正则 `r'def _verify_hash\(self\):.*?(?=\n(?:    def |class )|\Z)'` 使用 `\Z`（字符串末尾）作为 fallback 边界。当 `_verify_hash` 是类中最后一个方法时，类结束后是模块级代码（0 级缩进），`\n(?:    def |class )` 无法匹配，`.*?` 会一路扩展到 `\Z`，吞噬所有模块级代码，最终替换范围远超预期。

修复改为逐行遍历：
1. 找到 `    def _verify_hash(self):` 行（4 空格缩进，类方法级别）
2. 跳过该方法签名行及后续所有方法体行（空行或以 8+ 空格缩进开头的行）
3. 遇到第一个非空且缩进不足 8 空格的行时终止（即下一个类方法、类结束后的模块级代码、或文件结束）
4. 用 `def _verify_hash(self):\n        pass\n` 替换原始方法

同时增加了两个断言校验：
- 第 1 步后检查 `'openeuler'` 是否已写入 `getdeps_platform.py`
- 第 2 步后检查 `def _verify_hash(self):\n        pass\n` 是否已写入 `fetcher.py`

## 潜在风险
- 如果 `fetcher.py` 中 `_verify_hash` 方法有 decorator（装饰器），本修复不会匹配 decorator 行，但原正则同样不处理 decorator，故无新增风险。
- 如果 fbthrift v2026.06.08.00 中 `fetcher.py` 的方法体缩进不是标准 8 空格，替换可能失败并被 assert 捕获——这比原正则静默失败更安全，能及早发现问题。