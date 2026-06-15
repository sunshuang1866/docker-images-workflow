# 修复摘要

## 修复的问题
Dockerfile 中 COPY 进容器的 `.sh` 脚本缺少可执行权限，直接 `./xxx.sh` 调用导致 Permission denied (exit code 126)。

## 修改的文件
- `HPC/3dslicer/5.10.0/24.03-lts-sp3/Dockerfile`: 在 RUN 命令开头增加 `chmod +x *.sh`，为三个构建脚本赋予可执行权限后再调用。

## 修复逻辑
CI 分析报告指出根因是 `.sh` 文件在 Git 仓库中为 100644 模式（无执行位），COPY 进容器后权限仍为 644，shell 无法直接执行。在 RUN 指令开头追加 `chmod +x *.sh` 确保三个脚本（build-CTKAppLauncher.sh、build-tbb.sh、build-Slicer.sh）在执行前获得可执行权限，这是最小化且幂等的修复方案。

## 潜在风险
无。`chmod +x` 是幂等操作，对已有执行权限的文件无副作用。该修改仅影响 `/opt/` 下的 `.sh` 文件，不会影响镜像中其他文件。