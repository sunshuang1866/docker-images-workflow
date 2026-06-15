# 修复摘要

## 修复的问题
三个构建脚本（`build-CTKAppLauncher.sh`、`build-tbb.sh`、`build-Slicer.sh`）通过 `COPY` 指令复制到镜像后缺少可执行权限，导致 `RUN` 中直接执行 `./build-CTKAppLauncher.sh` 时返回 `Permission denied`（exit code 126）。

## 修改的文件
- `HPC/3dslicer/5.10.0/24.03-lts-sp3/Dockerfile`: 在 RUN 指令开头添加 `chmod +x` 为三个脚本赋予可执行权限

## 修复逻辑
在 Dockerfile 第 21 行 `RUN` 指令的最前面插入 `chmod +x ./build-CTKAppLauncher.sh ./build-tbb.sh ./build-Slicer.sh &&`，在执行脚本之前先为其添加可执行权限。这是 CI 分析报告推荐的方向 1（置信度: 高），改动最小，仅新增一行命令，不改变原有执行逻辑。

## 潜在风险
无。`chmod +x` 仅影响容器内 `/opt/` 目录下的脚本文件权限，不改变任何构建逻辑或依赖，不会对最终镜像产物产生副作用。