# 修复摘要

## 修复的问题
`fix_getdeps.py` 中用于跳过 `_verify_hash` 方法的正则表达式无法匹配上游 `fetcher.py` 中带返回类型注解 `-> None:` 的方法签名，导致 `_verify_hash` 补丁静默失败，本地预置的有效 tarball 被 SHA-256 校验失败后删除，进而触发从已失效的 pagure.io 下载 HTML 页面导致构建失败。

## 修改的文件
- `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/fix_getdeps.py`: 将 `_verify_hash` 方法的匹配正则从 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 改为 `r'def _verify_hash\(self\)[^:]*:.*?(?=\n    def )'`，使其兼容带 `-> None:` 返回类型注解的方法签名。

## 修复逻辑
上游 fbthrift v2026.06.08.00 的 `fetcher.py` 中 `_verify_hash` 方法签名为 `def _verify_hash(self) -> None:`（含类型注解），而原正则 `def _verify_hash\(self\):` 期望括号后紧跟冒号，导致匹配失败。新增的 `[^:]*` 允许在 `(self)` 和 `:` 之间匹配任意非冒号字符（即 ` -> None` 等可选类型注解），使得补丁能正确将整个方法体替换为 `pass`。当 `_verify_hash` 变为空操作后，`ArchiveFetcher.update()` 在发现 `downloads` 目录下已存在预置文件时不会因哈希校验失败删除该文件，从而跳过网络下载，直接使用本地有效 tarball 完成解压和编译。

## 潜在风险
无。修改仅放宽了正则匹配范围，使其同时兼容有/无类型注解的方法签名，不影响原有对 `getdeps_platform.py` 的发行版补丁逻辑。