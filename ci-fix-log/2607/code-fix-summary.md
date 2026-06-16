# 修复摘要

## 修复的问题
`fix_getdeps.py` 中用于跳过 `_verify_hash` 的正则表达式未匹配实际方法签名（含 `-> None` 返回类型注解），导致 verify_hash 补丁未生效，getdeps 因哈希校验失败删除了预置的 libaio 本地包并回退到 pagure.io 网络下载（返回 HTML），构建失败。

## 修改的文件
- `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/fix_getdeps.py`: 在第 17 行的正则表达式中，`\(self\):` 改为 `\(self\).*?:`，使模式可匹配 `def _verify_hash(self) -> None:` 签名（处理返回类型注解）。

## 修复逻辑
原始正则 `def _verify_hash\(self\):.*?(?=\n    def )` 要求 `(self)` 后紧跟 `:`，但 fbthrift 源码中 fetcher.py 的 `_verify_hash` 方法签名为 `def _verify_hash(self) -> None:`，两者之间还有 ` -> None`，导致正则匹配失败，`re.sub` 不执行任何替换。补丁未生效时，`_verify_hash` 仍计算文件 SHA256 并与 manifest 中的预期哈希比对；本地预置的 tar.gz 与 manifest 记录不同，校验失败后文件被删除，getdeps 转为从 pagure.io 下载（返回 HTML），最终 exit code 1。修改后正则 `def _verify_hash\(self\).*?:` 可匹配带或不带返回类型注解的方法签名，补丁正常将方法体替换为 `pass`，哈希校验被跳过，预置文件得以直接使用。

## 潜在风险
无。修复仅扩展正则匹配范围以包含返回类型注解，方法体替换逻辑不变，不影响 Dockerfile 中已正确的 cp 目标文件名及其他任何构建步骤。