# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），由 eulerpublisher 包内置的 `bwa_test.sh` 文件使用 CRLF 换行符导致 `bad interpreter` 错误。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出：Docker 镜像构建（Build + Push）已成功完成，失败发生在 eulerpublisher 框架的 CI [Check] 后测试阶段。根因是 eulerpublisher 包中 `tests/container/app/bwa_test.sh` 的 shebang 行因 CRLF 结尾被解释为 `/bin/sh\r`，导致系统找不到解释器。此问题与本 PR 的 4 个变更文件（Dockerfile、README.md、image-info.yml、meta.yml）完全无关，属于 CI 基础设施（eulerpublisher 软件包）层面问题，应由 CI 平台维护人员修复 `bwa_test.sh` 的换行符（CRLF → LF）后重新发布 eulerpublisher 包。

## 潜在风险
无