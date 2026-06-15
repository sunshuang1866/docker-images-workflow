# 修复摘要

## 修复的问题
`zlib.patch` 无法通过 `git apply` 应用到 Slicer v5.10.0（及 main 分支）的 `SuperBuild/External_zlib.cmake`，因为上游代码在 patch 第二 hunk 所在行（原第 48 行）附近的上下文已发生变化，导致 Docker 构建在补丁应用阶段中断。

## 修改的文件
- `HPC/3dslicer/5.10.0/24.03-lts-sp3/build-Slicer.sh`: 将 `git apply zlib.patch` 替换为等价的 `sed` 命令，避免因行号偏移或上下文微变导致的补丁应用失败

## 修复逻辑
分析报告指出两个方向：重新生成 patch（方向1）或移除补丁逻辑（方向2）。由于无上游源码无法重新生成 patch，且 aarch64 上 zlib 的 `-fPIC` 标志仍可能必要，采用等效替代方案：

1. 第一条 `sed` 命令在 `if(NOT DEFINED ZLIB_ROOT AND NOT Slicer_USE_SYSTEM_${proj})` 行之前插入 `${proj}_CMAKE_C_FLAGS` 变量定义及 64 位 `-fPIC` 条件逻辑
2. 第二条 `sed` 命令将 `-DCMAKE_C_FLAGS:STRING=${ep_common_c_flags}` 替换为 `-DCMAKE_C_FLAGS:STRING=${${proj}_CMAKE_C_FLAGS}`

这等价于原 `zlib.patch` 的两个 hunk 逻辑，但不依赖于精确行号和上下文完整性，`sed` 通过模式匹配定位目标行，对上游代码的位置变化更有弹性。

## 潜在风险
- 如果上游代码在后续版本中改变了 `if(NOT DEFINED ZLIB_ROOT...)` 行或 `-DCMAKE_C_FLAGS:STRING=${ep_common_c_flags}` 行的写法（例如变量名变更），`sed` 命令会静默无匹配（但不会导致脚本退出），zlib 仍使用默认 `ep_common_c_flags` 编译，在 aarch64 上可能因缺少 `-fPIC` 导致链接失败。该风险不高于当前已存在的失败状态