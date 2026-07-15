# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），系 eulerpublisher CI 工具包内置的 `bwa_test.sh` 测试脚本使用 Windows 风格 CRLF 换行符导致 shebang 解析失败。

## 修改的文件
无（PR 代码本身无需修改）

## 修复逻辑
CI 日志表明 Docker 镜像构建和推送均已成功完成，仅在 `[Check]` 阶段因 `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh` 脚本的 `#!/bin/sh` 行末尾附带 `\r`（CRLF 换行符），导致内核尝试查找 `#!/bin/sh\r` 解释器失败。此问题根源在 eulerpublisher 仓库中的测试脚本文件格式，与本 PR 新增的 bwa Dockerfile 及元数据文件无关。需由 eulerpublisher 维护者将 `bwa_test.sh` 的换行符从 CRLF 转换为 LF 后重新发布。

## 潜在风险
无