# 修复摘要

## 修复的问题
zlib.patch 的两个 hunk 在 Slicer v5.12.0 上游源码 `SuperBuild/External_zlib.cmake` 上无法应用（patch does not apply），因为 patch 是基于更旧版本的 Slicer 生成的，行号与上下文内容均不匹配。

## 修改的文件
- `HPC/3dslicer/5.12.0/24.03-lts-sp3/zlib.patch`: 基于 Slicer v5.12.0 上游仓库的实际 `SuperBuild/External_zlib.cmake` 内容重新生成 patch，修正两个 hunk 的上下文行号和周围内容。

## 修复逻辑
1. 从 Slicer 上游仓库（tag `v5.12.0`，对应 Dockerfile 中 `ARG VERSION=5.12.0`）获取了 `SuperBuild/External_zlib.cmake` 的实际内容。
2. Hunk 1 旧版问题：patch 期望 `if(DEFINED ZLIB_ROOT...)` 位于第 19 行，但 v5.12.0 中该行在第 18 行（offset -1）。已重新生成 hunk，使上下文精确匹配 v5.12.0 第 19-24 行内容。
3. Hunk 2 旧版问题：patch 期望 `-DCMAKE_C_FLAGS` 行后面紧跟 `-DZLIB_MANGLE_PREFIX`，但 v5.12.0 中该行后面是 `-DCMAKE_POSITION_INDEPENDENT_CODE:BOOL=ON`（上游已变更）。已重新生成 hunk，使上下文精确匹配 v5.12.0 第 49-55 行实际内容。
4. 已从上游 v5.12.0 获取 `SuperBuild/External_zlib.cmake` 验证，通过 `git apply --check` 和 `git apply` 双重验证，patch 可干净应用。

## 潜在风险
无。patch 的逻辑含义（为 64 位架构添加 `-fPIC` 编译标志、通过 `${${proj}_CMAKE_C_FLAGS}` 变量间接引用编译标志）与原始 patch 完全一致，仅修正了行号和上下文以适配 Slicer v5.12.0 上游源码。