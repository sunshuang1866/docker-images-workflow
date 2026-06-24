# 修复摘要

## 修复的问题
Dockerfile 中 COPY 的 shell 脚本缺少可执行权限，导致 RUN 步骤报 "Permission denied" (exit code 126)。

## 修改的文件
- `HPC/3dslicer/5.12.0/24.03-lts-sp3/Dockerfile`: 在 COPY 脚本指令之后、WORKDIR 之前，新增 `RUN chmod +x /opt/*.sh` 确保所有构建脚本具有可执行权限。

## 修复逻辑
CI 分析报告指出根因为：Dockerfile 通过 `COPY` 将 `build-CTKAppLauncher.sh`、`build-tbb.sh`、`build-Slicer.sh` 复制到 `/opt/` 目录，但源文件在 Git 仓库中无执行权限位（`100644`），COPY 指令保留源文件权限，导致直接 `./xxx.sh` 调用时被 Shell 拒绝执行。修复采用分析报告建议的"方向 1"：在 COPY 之后、执行之前增加 `RUN chmod +x /opt/*.sh`，以最小改动赋予脚本执行权限，不依赖 Git 文件模式。

## 潜在风险
无。`chmod +x /opt/*.sh` 仅影响 COPY 进 `/opt/` 目录的 `.sh` 文件，不会影响镜像中其他文件或后续构建步骤。