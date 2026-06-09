# 修复摘要

## 修复的问题
修复 `fix_getdeps.py` 中 `_verify_hash` 替换正则无法匹配「类中最后一个方法」的边界情况，导致 libaio tarball 哈希校验静默未被跳过。

## 修改的文件
- `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/fix_getdeps.py`: 扩展 regex 的 lookahead 边界，增加 `\nclass ` 和 `\Z` 两种终止条件

## 修复逻辑
原始正则 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 仅以「下一个 4 空格缩进的 `def `」作为匹配终止边界。当 `_verify_hash` 是该类中最后一个方法时，其后不存在同缩进级别的 `def`，正则无法匹配任何内容，`re.sub` 静默返回原字符串，`_verify_hash` 方法体未被替换为 `pass`，libaio tarball 的 SHA256 校验仍会执行，可能因校验失败导致构建中止。

修复后的正则 `r'def _verify_hash\(self\):.*?(?=\n(?:    def |class )|\Z)'` 增加两种终止条件：
- `\nclass `：当 `_verify_hash` 是类中最后一个方法，其后是下一个类定义
- `\Z`：当 `_verify_hash` 是文件最后一个方法，无后续内容

确保无论 `_verify_hash` 在类中的位置如何，其方法体都能被 `pass` 替换，跳过哈希校验。

## 潜在风险
无。原 regex 在 `_verify_hash` 非末方法时行为不变（`\n    def ` 仍是 lookahead 的首选项），仅覆盖了原本无法匹配的边界情况。