# 修复摘要

## 修复的问题
三个 Shell 脚本 (`build-CTKAppLauncher.sh`, `build-tbb.sh`, `build-Slicer.sh`) 在 git 仓库中缺少执行权限（模式 `100644`），导致 Docker 构建时 `./build-CTKAppLauncher.sh` 报 `Permission denied`，进程退出码 126。

## 修改的文件
- `HPC/3dslicer/5.10.0/24.03-lts-sp3/Dockerfile`: 在 COPY 脚本之后、RUN 执行脚本之前，新增 `RUN chmod +x` 命令，赋予三个脚本可执行权限。

## 修复逻辑
在 Dockerfile 的第 20–21 行之间新增一行 `RUN chmod +x ./build-CTKAppLauncher.sh ./build-tbb.sh ./build-Slicer.sh`。COPY 指令会将文件原样拷贝（保留 git 中的 `100644` 无执行权限模式），执行前通过 `chmod +x` 显式赋予可执行权限，使后续 `./script.sh` 调用不再因权限被拒绝而失败。这对应分析报告中方向 1（置信度：高）。

## 潜在风险
无。此修改仅增加一个 RUN 层，不影响构建逻辑和产物。