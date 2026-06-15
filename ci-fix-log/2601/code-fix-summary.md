# 修复摘要

## 修复的问题
Docker 构建时 `.sh` 脚本因缺少可执行权限导致 `Permission denied` (exit code 126)

## 修改的文件
- `HPC/3dslicer/5.10.0/24.03-lts-sp3/Dockerfile`: 在 COPY 三个 `.sh` 脚本后、RUN 执行脚本前，新增 `RUN chmod +x` 步骤赋予脚本可执行权限

## 修复逻辑
CI 分析报告指出：`COPY` 指令保留源文件的权限位，仓库中新增的 `.sh` 文件 Git 模式为 `100644`（不可执行），导致 Docker 构建时 `./build-CTKAppLauncher.sh` 报 Permission denied。修复方式是在所有 COPY 完成后、执行脚本前，添加 `RUN chmod +x /opt/build-CTKAppLauncher.sh /opt/build-tbb.sh /opt/build-Slicer.sh`，确保三个构建脚本在容器内具备可执行权限。这是报告推荐的方向 1（置信度：高），最小改动且直接解决根因。

## 潜在风险
无。`chmod +x` 仅影响权限位，不改变脚本内容或构建逻辑。