# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error）：openEuler 24.03-LTS-SP4 软件仓库镜像服务器 HTTP/2 协议异常，无需代码修改。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出失败类型为 `infra-error`，根因是 openEuler 24.03-LTS-SP4 软件仓库镜像在提供 RPM 包下载时多次返回 HTTP/2 协议层错误（`Curl error (92): INTERNAL_ERROR`），导致 `dnf install` 无法完成关键包（gcc、gcc-gfortran、glibc-devel 等）的下载。此问题与 PR 代码变更无关，PR 中的 Dockerfile 语法和包名均正确。重新触发 CI 构建即可。

## 潜在风险
无