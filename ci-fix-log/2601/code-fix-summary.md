# 修复摘要

## 修复的问题
`zlib.patch` 补丁文件与 Slicer v5.10.0 的 `SuperBuild/External_zlib.cmake` 不兼容，`git apply` 失败导致 Docker 构建中断。

## 修改的文件
- `HPC/3dslicer/5.10.0/24.03-lts-sp3/build-Slicer.sh`: 移除 `zlib_patch=$2` 参数及 `git apply zlib.patch` 相关代码块（原第 9 行、第 56-59 行）
- `HPC/3dslicer/5.10.0/24.03-lts-sp3/Dockerfile`: 移除 `COPY zlib.patch /opt/` 行，并将 `./build-Slicer.sh ${BRANCH} /opt/zlib.patch` 改为 `./build-Slicer.sh ${BRANCH}`

## 修复逻辑
Slicer v5.10.0 上游已在 `SuperBuild/External_zlib.cmake` 中添加了 `-DCMAKE_POSITION_INDEPENDENT_CODE:BOOL=ON`，该选项通过 CMake 内部机制为 zlib 编译自动添加 `-fPIC` 标志，原来手动注入 `-fPIC` 的 `zlib.patch` 已不再需要。同时 v5.10.0 对该 cmake 文件进行了多处修改（`ZLIB_MANGLE_PREFIX` → `ZLIB_SYMBOL_PREFIX`、新增 `ZLIB_COMPAT`/`ZLIB_ENABLE_TESTS`/`CMAKE_INSTALL_LIBDIR` 等选项），导致旧 patch 的上下文行号完全失效。因此移除 patch 是正确且最小的修复方案。

## 潜在风险
`zlib.patch` 文件保留在源码目录中但不再被使用。如果未来需要该补丁逻辑，应针对对应版本重新生成 patch。当前 v5.10.0 已通过 `CMAKE_POSITION_INDEPENDENT_CODE` 覆盖了原 patch 的 `-fPIC` 需求，无功能缺失风险。