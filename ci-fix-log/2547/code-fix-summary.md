# 修复摘要

## 修复的问题
`fix_getdeps.py` 中用于跳过 `_verify_hash` 哈希校验的正则表达式不匹配上游 fbthrift v2026.06.08.00 中 `fetcher.py` 的实际方法签名，导致 getdeps 对自定义 libaio tarball 做哈希校验失败。

## 修改的文件
- `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/fix_getdeps.py`: 修复 `re.sub` 的正则表达式，使其能匹配带有返回类型注解 `-> None:` 的 `_verify_hash` 方法签名，并添加 `\Z` 作为兜底结束条件

## 修复逻辑
上游 fbthrift 的 `build/fbcode_builder/getdeps/fetcher.py` 中 `_verify_hash` 方法的实际签名为 `def _verify_hash(self) -> None:`（带有 `-> None:` 返回类型注解）。但 `fix_getdeps.py` 中使用的正则表达式 `def _verify_hash\(self\):` 期望签名以 `):` 结尾，导致在 `)` 后遇到 ` -> None:` 时匹配失败，`re.sub` 未执行任何替换，哈希校验未被跳过，getdeps 对自定义 libaio 二进制 tarball 计算 sha256 后发现与 manifest 中预期值不匹配而报错退出。

修复方案：将正则从 `def _verify_hash\(self\):` 改为 `def _verify_hash\(self[^)]*\).*?:`，其中 `[^)]*` 处理括号内可能的额外参数，`.*?:` 处理返回类型注解到冒号之间的内容。同时在 lookahead 中添加 `|\Z` 作为兜底终止条件。

## 潜在风险
无。正则更改仅放宽了方法签名的匹配条件，替换行为不变。已验证新正则能正确匹配上游代码并将方法体替换为 `pass`，同时不破坏后续方法定义。