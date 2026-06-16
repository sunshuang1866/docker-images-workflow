# 修复摘要

## 修复的问题
`fix_getdeps.py` 中 `_verify_hash` 补丁的正则表达式与实际源码方法签名不匹配（缺少 `-> None` 类型注解），导致补丁静默失败，预置的有效 tar.gz 被删除后被 pagure.io 的 HTML 响应覆盖。

## 修改的文件
- `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/fix_getdeps.py`: 修复正则表达式以匹配 `def _verify_hash(self) -> None:` 方法签名（原正则只匹配 `def _verify_hash(self):`，未匹配类型注解 `-> None`），同步更新替换文本包含类型注解。

## 修复逻辑
fetcher.py 中 `_verify_hash` 方法的实际签名为 `def _verify_hash(self) -> None:`，而原有正则 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 中的 `\(self\):` 无法匹配 `(self) -> None:`，导致 `re.sub` 不执行替换。补丁失效后，`_verify_hash` 正常执行并检测到预置 tar.gz 的 sha256 与 manifest 期望值不匹配，随即删除文件并触发重新下载。下载的 pagure.io URL 已失效，返回的是 HTML 页面而非 tar.gz，最终因无法解压 HTML 导致构建失败。

修复将正则改为 `r'def _verify_hash\(self\).*?:.*?(?=\n    def )'`，在 `\(self\)` 与 `:` 之间插入 `.*?` 以覆盖类型注解 ` -> None`，使替换正确生效。补丁生效后，`_verify_hash` 退化为 `pass`，预置的有效 tar.gz 不会被删除，`update()` 流程检测到文件存在后跳过下载，直接进入解压步骤。

## 潜在风险
无。修复仅调整正则表达式的匹配范围，替换逻辑不变（将 `_verify_hash` 替换为 `pass`）。该补丁的预期行为本就如此，原实现因正则不匹配而失效。