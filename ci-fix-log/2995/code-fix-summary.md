# 修复摘要

## 修复的问题
无需代码修改。CI 失败类型为 `infra-error`，根因是 eulerpublisher 工具包内置测试脚本 `bwa_test.sh` 包含 Windows 风格换行符（CRLF），导致 shebang 行 `#!/bin/sh` 末尾携带不可见回车符（`^M`），系统无法识别解释器，报 `bad interpreter` 错误。

## 修改的文件
无。PR 代码变更（Dockerfile、README.md、image-info.yml、meta.yml）均与此次失败无关。Docker 镜像构建、推送阶段全部成功。

## 修复逻辑
此问题属于 CI 基础设施故障，应由 CI 运维人员修复 eulerpublisher 包中的 `bwa_test.sh`：将其行尾格式从 CRLF 转换为 LF（如 `dos2unix` 或 `sed -i 's/\r$//'`），然后重新安装或更新 eulerpublisher 包。PR 代码无需任何修改。

## 潜在风险
无