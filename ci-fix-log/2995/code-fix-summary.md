# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于 **infra-error**，根因是 CI 基础设施 `eulerpublisher` 包自带的 `bwa_test.sh` 测试脚本包含 Windows 风格行尾（CRLF），导致 shebang 解释器路径被解析为 `/bin/sh\r`（即 `/bin/sh^M`），Linux 内核无法找到该解释器，shell 报 "bad interpreter: No such file or directory"。

## 修改的文件
无。PR #2995 的原有的 4 个变更文件（Dockerfile、README.md、doc/image-info.yml、meta.yml）内容均正常，Docker 镜像构建和推送均已成功完成，无需修改。

## 修复逻辑
分析报告明确指出此失败与 PR 代码变更无关：
- Docker 镜像构建阶段（`#7 DONE 199.0s`）和推送阶段（`[Push] finished`）均成功
- 失败发生在构建后的 `[Check]` 测试阶段，调用的是 CI 工具 `eulerpublisher` 包内预装的 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 脚本
- 该脚本自身的 CRLF 行尾问题属于 CI 基础设施缺陷，需由 CI 管理员通过 `dos2unix` 或 `sed -i 's/\r$//'` 修复后重新部署 `eulerpublisher` 包

## 潜在风险
无。未对任何源码文件进行修改，不会引入风险。