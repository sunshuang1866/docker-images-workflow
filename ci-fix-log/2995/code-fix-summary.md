# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施故障（infra-error）：eulerpublisher 工具自带的 `tests/container/app/bwa_test.sh` 文件使用了 CRLF 行尾，导致 shebang `#!/bin/sh` 被误解析为 `#!/bin/sh\r`（日志中 `^M`），Shell 无法找到解释器，测试脚本执行失败。

## 修改的文件
无。

## 修复逻辑
此问题与 PR #2995 的代码变更无关。PR 新增的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml）均正确无误，Docker 镜像构建和推送已成功完成。失败发生在 CI 工具 eulerpublisher 的后处理阶段，属于 CI 基础设施问题，应由 eulerpublisher 维护者修复测试脚本的行尾格式（CRLF → LF），PR 作者无需修改任何代码。

## 潜在风险
无。