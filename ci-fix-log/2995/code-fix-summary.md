# 修复摘要

## 修复的问题
无代码修改。CI 失败原因为 CI runner 上的测试脚本 `bwa_test.sh` 包含 Windows 换行符（CRLF），属于 CI 基础设施问题，与本次 PR 代码变更无关。

## 修改的文件
无（infra-error，无需修改 PR 代码）

## 修复逻辑
CI 分析报告确认为 `infra-error`：测试脚本 `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh` 的 shebang 行被污染为 `#!/bin/sh\r`（末尾带 `^M` 回车符），Linux 内核无法找到解释器 `/bin/sh\r`，导致 `bad interpreter` 错误。

该文件位于 CI runner 的 `eulerpublisher` Python 包目录中，不属于本仓库。PR 所有变更（Dockerfile、README.md、image-info.yml、meta.yml）均仅涉及 bwa 镜像构建和文档更新，Docker 构建和推送阶段均已成功完成，仅 [Check] 测试阶段因 CI 环境问题失败。

修复需由运维人员在 CI 环境中将 `bwa_test.sh` 的换行符从 CRLF 转换为 LF（如执行 `dos2unix` 或 `sed -i 's/\r$//'`）。

## 潜在风险
无（无需代码修改）