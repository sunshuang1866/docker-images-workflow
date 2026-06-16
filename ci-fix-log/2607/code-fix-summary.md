# 修复摘要

## 修复的问题
`fix_getdeps.py` 中 `_verify_hash` 补丁的正则表达式无法匹配 fbthrift v2026.06.15.00 版本 `fetcher.py` 中的方法签名（含返回类型注解 `-> None`），导致哈希校验未被跳过，自定义 libaio tarball 因 SHA256 不匹配被拒绝。

## 修改的文件
- `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/fix_getdeps.py`: 将正则 `def _verify_hash\(self\):` 改为 `def _verify_hash\(self\).*?:`，使其能兼容带返回类型注解的方法签名

## 修复逻辑
fbthrift `fetcher.py` 中 `_verify_hash` 方法的实际签名为 `def _verify_hash(self) -> None:`，但原正则要求严格匹配 `def _verify_hash(self):`（不含类型注解）。正则无法命中，`re.sub` 返回原文不变，导致 `_verify_hash` 未被替换为 `pass`。构建时 getdeps 对自定义 libaio 源码包执行哈希校验失败。

修复在 `\(self\)` 和 `:` 之间添加 `.*?`，使其可匹配可选的方法返回类型注解（` -> None` 或无注解）。对应 CI 分析报告中的**方向 1**。

## 潜在风险
无。正则改动仅影响 `_verify_hash` 方法的匹配逻辑，`.*?` 非贪婪匹配不会溢出到其他方法。替换结果保持原有缩进和 Python 语法正确性。