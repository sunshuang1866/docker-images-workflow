# 修复摘要

## 修复的问题
无代码修改。此 CI 失败为 **infra-error**，由 CI 基础设施 `eulerpublisher` 包中的 `bwa_test.sh` 测试脚本使用 Windows 风格换行符（CRLF）导致，与 PR 中新增的 Dockerfile、README、image-info.yml、meta.yml 无关。Docker 镜像构建和推送均已成功完成。

## 修改的文件
无（infra-error，无需修改源码）

## 修复逻辑
CI 分析报告明确指出：
- Docker 镜像构建（`#7 DONE 199.0s`）和推送（`[Push] finished`）均成功
- 失败发生在 `eulerpublisher` 包的 Check 阶段，根因是测试脚本 `bwa_test.sh` 的 shebang 行末尾含 `\r`（CRLF），导致解释器路径被解析为 `/bin/sh\r`
- 该文件属于 CI 基础设施，不在本仓库中，也不在 PR 变更范围内

按照任务指令：**infra-error 无需代码修改，不要强行改代码**。应由 CI 基础设施维护方对 `eulerpublisher` 包中的 `bwa_test.sh` 执行 `dos2unix` 转换或在上游仓库中确保该文件以 LF 换行符存储。

## 潜在风险
无 — 未修改任何代码，不引入任何风险。待 CI 基础设施方修复 `bwa_test.sh` 的换行符问题后，此 PR 即可通过检查。