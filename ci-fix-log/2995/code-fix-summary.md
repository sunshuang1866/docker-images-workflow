# 修复摘要

## 修复的问题
CI 失败为 `infra-error`，根因是 eulerpublisher CI 工具内置的 `bwa_test.sh` 测试脚本包含 Windows 风格换行符（CRLF），与 PR #2995 的代码变更无关。无需修改任何 PR 文件。

## 修改的文件
无。此失败属于 CI 基础设施问题，不在 PR 代码范围内。

## 修复逻辑
CI 分析报告明确指出：
- 失败发生在 `[Check]` 阶段的 eulerpublisher 包内置脚本 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`
- 该脚本的 `#!/bin/sh` shebang 行因 CRLF 行尾携带 `\r` 字符，导致系统解析解释器路径为 `/bin/sh\r`，文件不存在，脚本启动失败
- Docker 镜像构建和推送均已成功完成，失败仅发生在 CI 管道后处理阶段
- 此问题与 PR #2995 的新增文件（Dockerfile、README.md、image-info.yml、meta.yml）均无关

修复应由 CI 基础设施维护者在 eulerpublisher 代码仓库中将 `bwa_test.sh` 的行尾格式从 CRLF 转换为 LF。

## 潜在风险
无