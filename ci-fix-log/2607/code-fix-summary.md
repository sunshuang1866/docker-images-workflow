# 修复摘要

## 修复的问题
getdeps.py 在构建 libaio 依赖时失败（exit code 1），通过安装系统 `libaio-devel` 让 getdeps `--allow-system-packages` 直接使用系统包，跳过源码构建。

## 修改的文件
- `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/Dockerfile`: 在 `dnf install` 列表中添加 `libaio-devel`

## 修复逻辑
上一个版本 v2026.05.18.00 使用相同的 Dockerfile 和 fix_getdeps.py 构建成功，说明根因不在我们的文件，而在 fbthrift v2026.06.15.00 源码中 libaio 的 manifest 或构建行为发生了变化（如下载 URL 变更、构建命令变更等），导致预下载的 tarball 文件名不匹配或构建命令不兼容。由于只能修改 PR 中的文件而无法修改 fbthrift 源码，最安全的最小化修复是：通过 dnf 安装 `libaio-devel`，让 getdeps 的 `--allow-system-packages` 功能检测到系统已安装 libaio，从而跳过从源码构建 libaio，直接使用系统库。

## 潜在风险
- 系统 `libaio-devel` 版本可能与 fbthrift 期望的版本存在 API 差异，但 libaio 是成熟稳定的 Linux 异步 I/O 库，API 保持向后兼容，风险极低
- 如果 fbthrift 源码中对 libaio 有特殊补丁需求（非标准行为），使用系统包可能会有功能差异，但 fbthrift 对 libaio 的使用一般是标准的异步 I/O 调用，不依赖特定补丁