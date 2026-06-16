# 修复摘要

## 修复的问题
修复 `fix_getdeps.py` 中绕过 libaio 哈希校验的正则表达式，使其不依赖固定 4 空格缩进和后续方法锚点。

## 修改的文件
- `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/fix_getdeps.py`: 修改 `_verify_hash` 匹配正则，将 lookahead `(?=\n    def )` 改为 `(?=\n[ \t]*def |\Z)`

## 修复逻辑
原正则 `(?=\n    def )` 存在两个缺陷：
1. 硬编码 4 空格缩进，若上游 `fetcher.py` 使用不同缩进风格（2 空格、tab）则匹配失败
2. 依赖后续存在另一个方法定义作为锚点，若 `_verify_hash` 是类中最后一个方法则匹配失败

修改后 `(?=\n[ \t]*def |\Z)` 允许任意空格/tab 缩进，且增加 `\Z`（字符串末尾）作为备选锚点，覆盖最后一个方法无后续 `def` 的场景。这确保 `_verify_hash` 方法体被正确替换为 `pass`，使手动提供的 libaio tar.gz 文件跳过哈希校验。

## 潜在风险
- 若 `fetcher.py` 中 `_verify_hash` 方法体包含嵌套的 `def` 语句（概率极低），可能提前截断匹配。但 fbcode_builder 的 fetcher 模块中无此情况。