# 修复摘要

## 修复的问题
Dockerfile 的 `dnf install` 命令遗漏 `tini` 包，导致容器启动时 `entrypoint.sh` 无法找到 `/usr/bin/tini`，容器立即退出，测试超时失败。

## 修改的文件
- `Bigdata/spark/4.1.2/24.03-lts-sp3/Dockerfile`: 在第 25 行的 `dnf install` 命令中追加 `tini` 包

## 修复逻辑
CI 分析报告指出 `entrypoint.sh` 的第 102 行和第 123 行均通过 `exec ... /usr/bin/tini -s -- "${CMD[@]}"` 使用 tini 作为 init 进程，但 Dockerfile 未安装该包。在 `dnf install` 命令末尾添加 `tini`，确保 `/usr/bin/tini` 二进制文件在容器运行时可用。若 openEuler 24.03-LTS-SP3 仓库中 `tini` 包名不同或不可用，则后续可能需要改为从 GitHub Release 下载静态二进制的方式安装。

## 潜在风险
- 若 openEuler 24.03-LTS-SP3 的 dnf 仓库中不存在 `tini` 包，`dnf install` 步骤将失败，构建会直接报错。此时需改用下载静态二进制的方式（参考 Apache Spark 官方 Dockerfile 做法）。
- 无其他风险，本次修改为在已有 `dnf install` 命令中追加一个依赖包，不影响其他功能。