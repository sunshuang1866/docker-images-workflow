# 修复摘要

## 修复的问题
pagure.io 对 libaio 源码包的下载请求返回 HTML 页面（含认证 Cookie），覆盖了 Dockerfile 中预置的本地 `libaio-libaio-0.3.113.tar.gz`，导致后续 tar.gz 提取失败。

## 修改的文件
- `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/fix_getdeps.py`: 在 `_download` 方法开头插入文件存在性检查，当本地文件已存在且大于 10KB 时跳过远程下载。

## 修复逻辑
分析报告指出 `fix_getdeps.py` 仅修补了 `_verify_hash` 方法跳过哈希校验，但未阻止 getdeps 的 fetcher 从远程 URL 重新下载文件。pagure.io 目前对 CI 请求返回带认证 Cookie 的 HTML（~2238 字节），下载到的 HTML 内容会覆盖 Dockerfile 中 `cp` 命令预置的本地正确 tar.gz。

修复方案：在 `_download` 方法（ArchiveFetcher 的实际下载入口）开头插入检查逻辑——如果 `self.file_name` 路径已存在文件且文件大小大于 10000 字节（排除 HTML 响应约 2KB 的情况），则直接 return 跳过远程下载。此阈值为有效 tar.gz（通常数百 KB）与 HTML 错误页（~2KB）之间提供了足够的区分度。

同时保留了原有的 `_verify_hash` 补丁及下载失败时的回退逻辑，确保其他未预置本地包的依赖仍可正常下载。

## 潜在风险
- 如果其他非 libaio 依赖也需要本地预置包但文件恰好小于 10KB，可能会被误判为无效文件而重新下载。根据当前 Dockerfile 设计，仅 libaio 使用了本地预置策略，此风险在当前场景下不存在。
- 正则匹配依赖 `def _download(self) -> None:` 的精确签名；若 fbthrift 未来版本修改了类型注解格式（如删去 `-> None`），补丁将静默失效，但不会破坏构建（仅回退到原有行为）。