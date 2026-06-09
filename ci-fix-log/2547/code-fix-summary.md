# 修复摘要

## 修复的问题
`fix_getdeps.py` 中的正则表达式未能匹配 `_verify_hash` 方法签名，导致哈希校验补丁未生效，getdeps 对预置 libaio tarball 进行哈希校验失败后删除本地文件并尝试从 pagure.io 网络下载，而 pagure.io 返回 HTML 页面导致构建失败。

## 修改的文件
- `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/fix_getdeps.py`: 修复第 17 行正则表达式，使其能匹配带类型注解的 `_verify_hash` 方法签名

## 修复逻辑
原始正则 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 要求方法签名必须是 `def _verify_hash(self):`（冒号紧跟在 `(self)` 之后），但 fbthrift v2026.06.08.00 的 `fetcher.py` 源码中实际签名为 `def _verify_hash(self) -> None:`（包含 `-> None:` 类型注解），导致正则无法匹配，`re.sub` 替换失败，`_verify_hash` 方法未被替换为 no-op。修改后的正则 `r'def _verify_hash\(self\).*:.*?(?=\n    def )'` 在 `(self)` 和 `:` 之间使用 `.*` 通配可选的类型注解部分，使正则能正确匹配并替换方法体。

## 潜在风险
- 正则中 `.*` 可能匹配到方法签名中额外的意外字符，但就当前 fbthrift 源码而言，方法签名为标准 Python 格式，不存在此类风险。
- Dockerfile 中 cp 目标文件名 `libaio-libaio-libaio-0.3.113.tar.gz` 已包含正确的三前缀格式，与 getdeps 期望的文件名一致，无需修改。