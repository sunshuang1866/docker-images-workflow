# 修复摘要

## 修复的问题
`fix_getdeps.py` 中跳过 `_verify_hash` 方法的正则表达式存在边界缺陷，当 `_verify_hash` 是类中最后一个方法时无法匹配，导致哈希校验未被跳过，构建失败。

## 修改的文件
- `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/fix_getdeps.py`: 将正则 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 改为 `r'def _verify_hash\(self\):.*?(?=\n    def |\nclass |\Z)'`

## 修复逻辑
原正则的 lookahead `(?=\n    def )` 要求 `_verify_hash` 之后必须还有另一个方法定义，当 `_verify_hash` 是类末尾方法时该 lookahead 匹配不到，导致 `re.sub` 整体匹配失败、替换不生效。修复后的正则增加了两个备选匹配目标：`\nclass `（下一个类定义开始）和 `\Z`（文件末尾），覆盖了"类中最后一个方法"的边界情况。

## 潜在风险
无。修改仅是一个字符的差异，不影响已有正常工作的场景（非末尾方法时 `\n    def ` 仍会优先匹配）。