# 修复摘要

## 修复的问题
无需代码修改。此 CI 失败属于**基础设施问题（infra-error）**，与本次 PR 变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败发生在 `[Check]` 阶段，由 `eulerpublisher` 工具中的测试脚本 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh` 包含 Windows 风格 CRLF 换行符导致。shebang 行 `#!/bin/sh` 被解析为 `#!/bin/sh\r`，内核无法找到该解释器路径，报 `bad interpreter: No such file or directory`。

Docker 镜像构建（`[Build]`）和推送（`[Push]`）阶段均已成功完成。失败的测试脚本位于 CI 工具 `eulerpublisher` 的安装目录中，不属于本次 PR 的任何提交文件。PR 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及修改了 README、image-info.yml、meta.yml 等元数据文件，未涉及任何测试脚本。

此问题需要 CI 运维团队处理：对 `eulerpublisher` 工具包中的 `bwa_test.sh` 文件执行换行符转换（CRLF → LF），然后重新部署 `eulerpublisher` 包。

## 潜在风险
无（未修改任何代码）