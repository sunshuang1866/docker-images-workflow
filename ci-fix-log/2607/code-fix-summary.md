# 修复摘要

## 修复的问题
`fix_getdeps.py` 中 `_verify_hash` 的正则表达式无法匹配新版本 fetcher.py 中带类型注解 `-> None` 的函数签名，导致哈希校验跳过补丁未生效，预置的正确 tarball 被 pagure.io 返回的 HTML 内容覆盖。

## 修改的文件
- `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/fix_getdeps.py`: 更新 `_verify_hash` 方法的匹配正则，使其兼容带返回类型注解的函数签名

## 修复逻辑
fbthrift v2026.06.15.00 的 `fetcher.py` 中 `_verify_hash` 方法签名变更为 `def _verify_hash(self) -> None:`（增加了 `-> None` 类型注解）。原正则 `def _verify_hash\(self\):.*?(?=\n    def )` 要求 `(self)` 后紧跟 `:`，无法匹配新签名，导致该补丁静默失败。

修改后的正则 `def _verify_hash\(self\)(?:\s*->\s*\w+)?:.*?(?=\n    def )` 使用可选非捕获组 `(?:\s*->\s*\w+)?` 匹配可选的 ` -> None` 部分，同时兼容旧版无类型注解的签名。

当 `_verify_hash` 被正确补丁为空操作后，`ArchiveFetcher.update()` 的逻辑为：文件已存在于 downloads 目录 → 调用 `_verify_hash()`（空操作，不抛出异常）→ 文件仍存在 → 跳过下载，直接使用预置的正确 tarball。

## 潜在风险
无。此修改仅扩展了正则表达式的匹配范围以兼容新语法，不改变补丁的语义（将 `_verify_hash` 替换为空操作）。该正则同时兼容旧版本 fbthrift 的函数签名，向后兼容。