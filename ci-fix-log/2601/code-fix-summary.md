# 修复摘要

## 修复的问题
Docker 镜像构建时三个 Shell 脚本因缺少执行权限导致 `Permission denied` (exit code 126)。

## 修改的文件
- `HPC/3dslicer/5.10.0/24.03-lts-sp3/Dockerfile`: 在 COPY 三个脚本之后、RUN 执行脚本之前，新增 `RUN chmod +x` 赋予执行权限。

## 修复逻辑
根因是 COPY 指令保留源文件的权限位，而三个 `.sh` 脚本在 git 中为 `644`（无执行权限），导致镜像内脚本不可执行。在 Dockerfile 中 COPY 后添加 `RUN chmod +x /opt/build-CTKAppLauncher.sh /opt/build-tbb.sh /opt/build-Slicer.sh`，使脚本在后续 `./script.sh` 调用前获得执行权限。此方案与 CI 分析报告中置信度最高的方向 1 一致，且仅新增一个 RUN 层，改动最小。

## 潜在风险
无。`chmod +x` 是幂等操作，不影响其他文件或后续构建步骤。