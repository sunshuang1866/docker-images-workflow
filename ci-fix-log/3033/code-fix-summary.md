# 修复摘要

## 修复的问题
修复 SeisSol 在 aarch64 架构上构建失败的问题（x86_64 专属编译标志 `-mno-red-zone` 不被 GCC 识别），并修复 `$LD_LIBRARY_PATH` 未定义变量 lint 警告。

## 修改的文件
- `HPC/seissol/202103.Sumatra/24.03-lts-sp4/Dockerfile`:
  1. 在第 62 行新增架构判断 `if [ "$(uname -m)" = "aarch64" ]`，在 aarch64 上通过 sed 删除上游 CMakeLists.txt 中注入 `-mno-red-zone` 的代码块（注释行 `# Generated code does only work without red-zone.` 至 `endif()`）
  2. 将第 99 行 `ENV LD_LIBRARY_PATH=...:${LD_LIBRARY_PATH:-}` 改为 `ENV LD_LIBRARY_PATH=...`，移除对未定义变量的引用

## 修复逻辑
CI 失败分析报告指出两个问题：

**问题 1（主）：`-mno-red-zone` 构建错误**
- 根因：SeisSol 上游 `CMakeLists.txt` 在 `HAS_REDZONE` 为 ON 时向 `subroutine.cpp` 的编译参数注入 `-mno-red-zone`。`HAS_REDZONE` 在 `cmake/cpu_arch_flags.cmake` 中默认为 ON，当 `-DHOST_ARCH=noarch` 时不匹配任何特定架构的 elseif 分支，导致 `HAS_REDZONE` 保持 ON。在 aarch64 上该标志不被 GCC 支持。
- 修复：在 Dockerfile 中，cmake 配置前通过 `uname -m` 判断当前架构，若为 aarch64 则用 sed 删除 CMakeLists.txt 中注入 `-mno-red-zone` 的整个条件块（4行）。在 aarch64 上不存在 x86_64 的 red zone 概念，移除该块无任何影响。在 x86_64 上不执行该 sed，保留原行为。
- 验证：已从上游 `https://raw.githubusercontent.com/SeisSol/SeisSol/202103_Sumatra/CMakeLists.txt` 获取源文件，用 Python 确认正则 `^# Generated code does only work without red-zone\.$` 至 `^endif()$` 匹配成功。

**问题 2（次）：`$LD_LIBRARY_PATH` 未定义变量警告**
- 根因：Dockerfile 中 `ENV LD_LIBRARY_PATH=...:${LD_LIBRARY_PATH:-}` 引用了在构建阶段未定义的变量，lint 工具报告 `UndefinedVar` 警告。
- 修复：移除 `${LD_LIBRARY_PATH:-}` 尾缀，基础镜像中 LD_LIBRARY_PATH 通常未设置，直接设置固定值即可。

## 潜在风险
- x86_64 构建不受影响（aarch64 条件判断不会执行 sed）。
- 移除 `${LD_LIBRARY_PATH:-}` 后，若基础镜像未来预设了 LD_LIBRARY_PATH，则其值会被覆盖（当前 openEuler 基础镜像未预设该变量，无实际影响）。