# 修复摘要

## 修复的问题
`zlib.patch` 无法应用于 3D Slicer v5.10.0 源码，导致 `build-Slicer.sh` 中 `git apply` 失败。v5.10.0 上游已将 `-DZLIB_MANGLE_PREFIX` 改为 `-DZLIB_SYMBOL_PREFIX` 并新增了 `-DCMAKE_POSITION_INDEPENDENT_CODE:BOOL=ON`，patch 上下文不匹配。

## 修改的文件
- `HPC/3dslicer/5.10.0/24.03-lts-sp3/build-Slicer.sh`: 删除 `git apply zlib.patch` 及其相关的 `cd`/`mv` 操作（原第56-59行）
- `HPC/3dslicer/5.10.0/24.03-lts-sp3/Dockerfile`: 删除 `COPY zlib.patch /opt/`，并将 `build-Slicer.sh` 调用中的 `/opt/zlib.patch` 参数移除

## 修复逻辑
CI 分析报告根因：`zlib.patch` 的第二个 hunk（针对 `SuperBuild/External_zlib.cmake`）无法应用于 v5.10.0 源码。经检查 v5.10.0 实际源码发现：

1. 上游已将 `-DZLIB_MANGLE_PREFIX:STRING=slicer_zlib_` 改为 `-DZLIB_SYMBOL_PREFIX:STRING=slicer_zlib_`，导致 patch 上下文不匹配
2. 上游已新增 `-DCMAKE_POSITION_INDEPENDENT_CODE:BOOL=ON`，该选项已确保 64 位构建包含位置无关代码（替代了 patch 中 `-fPIC` 的作用）

因此，patch 的用途（为 64 位构建添加 PIC 支持）在 v5.10.0 中已被上游解决，直接移除 patch 应用即可。

## 潜在风险
- aarch64 架构下代码路径相同（Dockerfile 中 arm64 分支仅修改 BRANCH 变量），不受影响
- 如果 v5.10.0 的 zlib 构建在某平台下仍因缺少 PIC 而失败（理论上不应发生，因 `CMAKE_POSITION_INDEPENDENT_CODE=ON` 已覆盖），则需重新生成匹配 v5.10.0 的 patch 文件