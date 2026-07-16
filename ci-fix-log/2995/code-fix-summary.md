# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 infra-error，由 CI runner 上部署的 eulerpublisher 测试脚本 `bwa_test.sh` 包含 Windows 风格换行符（CRLF）导致。

## 修改的文件
无。本次 PR 的代码变更（Dockerfile、README.md、image-info.yml、meta.yml）均正确，Docker 构建和推送已成功完成，无需修改。

## 修复逻辑
CI 分析报告确认：
1. Docker 镜像构建 `[Build] finished` 和推送 `[Push] finished` 均已成功
2. 失败发生在 CI 基础设施的 `[Check]` 阶段——`eulerpublisher` 工具尝试运行 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`，但该脚本 shebang 行末尾的 `\r`（CRLF 的 `^M`）导致内核寻找 `/bin/sh\r` 作为解释器，引发 `bad interpreter: No such file or directory`
3. 此问题与 PR 代码变更完全无关，属于 CI runner 上 eulerpublisher 包的部署问题

**需由 CI 基础设施团队处理**：对 `bwa_test.sh` 执行 `dos2unix` 或 `sed -i 's/\r$//'` 后重新部署 eulerpublisher 包。

## 潜在风险
无。本次未修改任何源代码。