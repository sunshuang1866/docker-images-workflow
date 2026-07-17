# 修复摘要

## 修复的问题
无需修改代码。CI 失败为基础设施问题（infra-error），与本次 PR 变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败的直接原因是 eulerpublisher 包中的测试脚本 `bwa_test.sh` 第一行 shebang 末尾包含 Windows 回车符 `\r`（`^M`），导致内核尝试查找 `/bin/sh\r` 解释器而失败。该文件位于 eulerpublisher 仓库 (`/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`)，不属于本仓库 (openeuler-docker-images) 的文件。

PR #2995 涉及的 4 个文件（Dockerfile、README.md、image-info.yml、meta.yml）均为 bwa 0.7.18 的 openEuler 24.03-LTS-SP4 支持配置，内容正确无语法错误，且 Docker 构建与推送阶段均已成功。失败仅发生在 CI 编排工具 eulerpublisher 执行测试脚本阶段，属于 CI 基础设施的 CRLF 文件格式问题。

**修复应由 eulerpublisher 仓库维护者执行**：将 `bwa_test.sh` 的行尾从 CRLF 转换为 LF（Unix 格式），使用 `dos2unix` 或 `sed -i 's/\r$//'` 处理后重新发布 eulerpublisher 包即可。

## 潜在风险
无。本仓库代码无需任何修改。