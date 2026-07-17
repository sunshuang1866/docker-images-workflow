# 修复摘要

## 修复的问题
无需代码修改——CI 失败为基础设施问题（infra-error），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出失败类型为 `infra-error`，根因是 eulerpublisher 包自带的 `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh` 脚本使用了 Windows 风格的 CRLF 换行符，导致 shebang 行被解析为 `/bin/sh\r` 而触发 `bad interpreter: No such file or directory`。

该测试脚本不属于本仓库，PR 变更的 4 个文件（Dockerfile、README.md、image-info.yml、meta.yml）均不涉及此文件，且 Docker 镜像的构建和推送阶段均已成功完成。此为 eulerpublisher 包/CI 基础设施侧的问题，需在基础设施仓库中将 `bwa_test.sh` 的换行符从 CRLF 转换为 LF（使用 `dos2unix` 或 `sed -i 's/\r$//'`）。

根据规范要求，`infra-error` 类型的失败不需要对源码仓库做任何代码修改。

## 潜在风险
无