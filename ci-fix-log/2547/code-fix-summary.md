# 修复摘要

## 修复的问题
`pagure.io` 源对 libaio 归档包返回 HTML 页面（而非有效 tar.gz），getdeps 下载 HTML 内容后覆盖了 Dockerfile 中预置的有效 libaio 文件，导致构建失败。

## 修改的文件
- `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/fix_getdeps.py`: 新增对 `fetcher.py` 中 `_download` 方法的 monkey-patch，当目标文件已存在且体积超过 10000 字节时跳过网络下载直接返回。

## 修复逻辑
原有的 `fix_getdeps.py` 仅 patch 了 `_verify_hash` 方法（跳过哈希校验），但 `_download` 方法仍会执行下载动作，从 `pagure.io` 拉取 HTML 内容并覆盖 Dockerfile 预置的有效 tar.gz 文件。

新增的 patch 在 `_download` 方法开头插入文件存在性检查：
- 若 `self.file_name` 已存在且体积 > 10000 字节（有效 tar.gz 远大于 2238 字节的 HTML 错误页面），直接 `return`，跳过下载。
- 对于其他依赖（文件不存在），原下载逻辑不受影响。

此修复与分析报告中的「方向 1」一致：在 `download` 方法层面拦截 libaio 的下载请求。

## 潜在风险
- `fetcher.py` 中的 `_download` 方法签名和 `self.file_name` 属性依赖 getdeps 内部实现（`ArchiveFetcher` 类）。若未来 getdeps 版本变更方法签名或文件路径属性名，此 patch 可能失效。当前版本经确认使用 `def _download(self) -> None:` 签名和 `self.file_name` 属性。
- `_download_dir()` 目录创建逻辑在早期返回时被跳过，但 Dockerfile 已通过 `mkdir -p` 预先创建了 downloads 目录，因此无影响。