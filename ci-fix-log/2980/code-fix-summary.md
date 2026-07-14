# 修复摘要

## 修复的问题
无需代码修改。CI 失败根因为 openEuler 24.03-LTS-SP4 官方 RPM 仓库镜像在提供 `gcc-c++` 等软件包下载时出现间歇性 HTTP/2 协议流错误（Curl error 92），属于上游基础设施问题。

## 修改的文件
无代码修改。

## 修复逻辑
CI 分析报告已将失败类型分类为 `infra-error`，失败原因是 openEuler 24.03-LTS-SP4 RPM 仓库的 CDN/镜像节点 HTTP/2 服务不稳定，与 PR 中新增的 Dockerfile 代码无关。Dockerfile 中的 `dnf install` 命令语法和包名均正确。应在上游镜像恢复稳定后重新触发 CI 构建（retest）。

## 潜在风险
无