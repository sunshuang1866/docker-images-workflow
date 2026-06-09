# 修复摘要

## 修复的问题
修复 `fix_getdeps.py` 中 `_verify_hash` 方法体的正则替换在 `_verify_hash` 为类中最后一个方法时无法匹配的 bug，导致哈希校验未禁用、预置 libaio tarball 被拒绝、getdeps.py 尝试从 pagure.io 下载 HTML 页面而构建失败。

## 修改的文件
- `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/fix_getdeps.py`: 增强 `_verify_hash` 补丁逻辑，增加 `\Z` 和 `\nclass ` 前瞻锚点作为额外匹配条件，并添加基于行的回退逻辑作为二次保障。

## 修复逻辑
CI 分析报告指出的根因：原正则 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 依赖 `_verify_hash` 之后存在另一个同缩进级别的 `def` 方法作为前瞻锚点。若 `_verify_hash` 是类中最后一个方法，前瞻永远不匹配，导致 `re.sub` 是空操作，哈希校验未被禁用。

修复采用两层策略：
1. 将前瞻锚点扩展为 `(?=\n    def |\nclass |\Z)`，增加对类定义边界和文件末尾的支持。
2. 增加回退逻辑：若正则仍未匹配（例如 _verify_hash 后存在非 def/class 的同级代码），使用行级遍历，根据缩进级别精确识别方法体边界并替换为 `pass`。

## 潜在风险
- 正则中使用 `\Z` 时，`.*?` 在无 `\n    def` 或 `\nclass` 匹配的情况下会匹配到文件末尾，此时若 `_verify_hash` 与 EOF 之间存在其他顶层代码，会被误替换。但实际 `fetcher.py` 文件中方法之后通常直接跟随下一个方法或类定义，此风险极低。
- 回退逻辑依赖 indentation 判断方法体边界，若文件存在混合 tab/space 缩进可能判断错误，但 Python 项目通常使用统一空格缩进，此风险很低。