# 修复摘要

## 修复的问题
`zlib.patch` 补丁无法应用到 Slicer v5.10.0 的 `SuperBuild/External_zlib.cmake`，因为上游已在 v5.10.0 中内置了 `-DCMAKE_POSITION_INDEPENDENT_CODE:BOOL=ON`（等效于 `-fPIC`），补丁不再必要。

## 修改的文件
- `HPC/3dslicer/5.10.0/24.03-lts-sp3/build-Slicer.sh`: 移除 `zlib_patch` 参数接收逻辑和 `git apply zlib.patch` 相关代码块
- `HPC/3dslicer/5.10.0/24.03-lts-sp3/Dockerfile`: 移除 `COPY zlib.patch /opt/` 行，并将 `build-Slicer.sh` 调用参数从 `${BRANCH} /opt/zlib.patch` 改为仅 `${BRANCH}`

## 修复逻辑
CI 分析报告指出根因是 `zlib.patch` 的第二处 hunk（行48附近）与 Slicer `v5.10.0` tag 中实际的 `SuperBuild/External_zlib.cmake` 内容不匹配。经对比确认，v5.10.0 的上游文件已包含 `-DCMAKE_POSITION_INDEPENDENT_CODE:BOOL=ON`，该 CMake 选项在 GCC 上会添加 `-fPIC` 标志，与原补丁的目标完全一致。因此该补丁已过时，移除补丁应用逻辑即可解决问题。

## 潜在风险
无。`-DCMAKE_POSITION_INDEPENDENT_CODE:BOOL=ON` 在 CMake 中跨编译器通用，在所有目标平台上（包括 arm64）与原有 `-fPIC` 补丁效果等价。