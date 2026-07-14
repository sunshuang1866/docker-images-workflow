# 修复摘要

## 修复的问题
无代码修改。此 CI 失败为 infra-error，失败原因是 CI 基础设施中 eulerpublisher 软件包自带的 `bwa_test.sh` 测试脚本存在 CRLF 换行符问题（shebang 行被解析为 `/bin/sh\r`），与本次 PR 的代码变更无关。

## 修改的文件
无。PR 涉及的文件（Dockerfile、README.md、image-info.yml、meta.yml）均无问题，无需修改。

## 修复逻辑
CI 分析报告明确指出：
- 失败发生在 CI 流水线的 [Check] 测试阶段，而非 [Build] 或 [Push] 阶段。
- Docker 镜像构建与推送均已成功完成，日志中 [Build] finished 和 [Push] finished 均有正常输出。
- 根因是 eulerpublisher Python 包中 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 的换行符格式问题（CRLF），与本次 PR 的 bwa Dockerfile 及元数据变更无关。
- 分析报告结论为"无关"，失败类型标注为 `infra-error`。

此问题需由 CI 基础设施维护方修复 eulerpublisher 测试脚本的换行符格式（如通过 `dos2unix` 或 `sed -i 's/\r$//'` 处理），或在 CI 流水线中调用测试脚本前自动转换。不属于本仓库代码层面的修复范围。

## 潜在风险
无。未对任何源码文件进行修改。