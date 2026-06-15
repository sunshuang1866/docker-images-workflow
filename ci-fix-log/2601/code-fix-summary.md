# 修复摘要

## 修复的问题
Dockerfile 中 COPY 构建脚本后缺少 `chmod +x`，导致执行时 `Permission denied` (exit code 126)。

## 修改的文件
- `HPC/3dslicer/5.10.0/24.03-lts-sp3/Dockerfile`: 在 COPY 三个构建脚本之后、RUN 执行之前，添加 `RUN chmod +x /opt/build-CTKAppLauncher.sh /opt/build-tbb.sh /opt/build-Slicer.sh`。

## 修复逻辑
Docker `COPY` 指令保留源文件权限，且构建脚本在源码仓库中可能没有可执行权限。在 `RUN` 执行脚本前添加 `chmod +x` 赋予执行权限，即可解决 `Permission denied` 错误。这与 CI 分析报告中的方向 1 一致。

## 潜在风险
无。