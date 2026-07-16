# 修复摘要

## 修复的问题
无需代码修改。此为 CI 基础设施问题（infra-error），openEuler 24.03-LTS-SP4 的 RPM 镜像站在 HTTP/2 协议层面不稳定，导致部分较大软件包（cmake-data、git-core、gcc-c++）下载时 HTTP/2 stream 被服务端非正常关闭（INTERNAL_ERROR），dnf 重试所有镜像后失败。

## 修改的文件
无。PR 中的 Dockerfile 语法正确、依赖声明合理，故障原因在 CI 外部。

## 修复逻辑
分析报告确认失败类型为 `infra-error`，置信度高。错误根源为 openEuler 镜像站的 HTTP/2 服务端协议异常，与 Dockerfile 代码无关。根据修复原则中的"如果分析报告指出是 infra-error，在 output_file 中说明无需代码修改，不要强行改代码"，本次不做任何代码修改。建议重试 CI 构建任务（re-trigger），待镜像站恢复后构建应当通过。

## 潜在风险
无。