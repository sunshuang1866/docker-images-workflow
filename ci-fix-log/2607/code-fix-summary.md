# 修复摘要

## 修复的问题
修复 `fix_getdeps.py` 中 `_verify_hash` 方法替换正则，使其在 `_verify_hash` 为类中最后一个方法时也能正确匹配并跳过哈希校验。

## 修改的文件
- `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/fix_getdeps.py`: 将替换 `_verify_hash` 的正则从依赖后续 `def` 边界的 lookahead 模式改为显式匹配方法体缩进行模式。

## 修复逻辑
原正则使用 `re.DOTALL` + `.*?` + lookahead `(?=\n    def )`，要求 `_verify_hash` 之后必须存在另一个 `def` 方法作为匹配边界。当 `_verify_hash` 是所在类的最后一个方法时，lookahead 找不到 `\n    def `，正则整体无法匹配，导致原始哈希校验代码未被替换为 `pass`，最终 getdeps 在校验本地提供的 `libaio-libaio-0.3.113.tar.gz` 时因哈希值与上游 manifest 不匹配而失败。

修复后的正则以 `def _verify_hash\(self\):\n` 开头，接着用 `(?:        [^\n]*\n|[ \t]*\n)*` 显式匹配方法体中的每条缩进行（8空格开头）和空白行，不依赖方法是否为最后一个。移除了 `re.DOTALL` 依赖，改用显式 `\n` 匹配，确保无论 `_verify_hash` 在类中的位置如何都能正确替换。

## 潜在风险
无。新正则的行为与原正则（当它成功匹配时）等价：均将 `_verify_hash` 方法体替换为 `pass`。方法间的空白行可能被缩减，但 Python 不要求方法间必须有空白行，不影响代码正确性。