# 修复摘要

## 修复的问题
CI 基础设施问题，无需代码修改。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告确认此为 `infra-error`：失败发生在 CI 流水线的 `[Check]` 阶段，根因是 eulerpublisher 测试框架中的 `bwa_test.sh` 脚本携带 Windows 风格 CRLF 行尾符，导致 shebang 被错误解析为 `/bin/sh\r`，触发 "bad interpreter" 错误。

该问题与 PR #2995 的代码变更完全无关：Dockerfile 构建全程成功，镜像推送也成功。PR 作者无法通过修改仓库内的 Dockerfile、README.md、image-info.yml 或 meta.yml 解决此问题。

此问题应由 CI 基础设施维护者在 eulerpublisher 仓库中将 `tests/container/app/bwa_test.sh` 的行尾从 CRLF 转换为 LF 后，重新触发 CI 流水线即可。

## 潜在风险
无