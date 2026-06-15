# 修复摘要

## 修复的问题
Docker 镜像构建时 `.sh` 脚本无执行权限，导致 `RUN` 以 `./` 方式执行时报 `Permission denied`（exit code 126）。

## 修改的文件
- `HPC/3dslicer/5.10.0/24.03-lts-sp3/Dockerfile`: 在 COPY 指令之后、RUN 执行脚本之前，新增一行 `RUN chmod +x` 为三个构建脚本赋予可执行权限。

## 修复逻辑
CI 分析报告指出：三个 `.sh` 脚本通过 `COPY` 进入镜像后，保留了 git 仓库中的文件权限（`100644`，无执行位），导致 Shell 无法以 `./` 方式直接执行。修复采用分析报告中的「方向 1」，在 `Dockerfile` 第 20 行新增 `RUN chmod +x /opt/build-CTKAppLauncher.sh /opt/build-tbb.sh /opt/build-Slicer.sh`，在脚本被调用前赋予可执行权限。此改动为最小化修改（仅新增 1 行），不影响其他逻辑。

## 潜在风险
无。