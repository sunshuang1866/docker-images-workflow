# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施问题（infra-error），与本次 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出：
- 失败类型为 `infra-error`，失败发生在 CI 流水线的 [Check] 测试阶段
- 根因是 eulerpublisher 软件包内的 `bwa_test.sh` 测试脚本含有 CRLF 换行符（Windows 风格），导致 shebang 行解析为 `/bin/sh\r`，系统报 "bad interpreter: No such file or directory"
- 与 PR 变更**无关**：PR 仅涉及 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`、`HPC/bwa/README.md`、`HPC/bwa/doc/image-info.yml`、`HPC/bwa/meta.yml`，Docker 镜像构建与推送均已成功完成

此问题需要在 CI 基础设施层面修复（eulerpublisher 软件包或 CI 流水线），不在本次 PR 代码修改范围内。强行修改源码库文件无法解决此问题。

## 潜在风险
无