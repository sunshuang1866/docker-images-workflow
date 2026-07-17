# 修复摘要

## 修复的问题
无需代码修复。CI 失败为基础设施问题（infra-error）：openEuler 24.03-LTS-SP4 仓库在构建期间出现 HTTP/2 流帧错误，导致 `dnf install` 下载 RPM 包失败。

## 修改的文件
无（infra-error，无需代码修改）

## 修复逻辑
CI 失败分析报告确认根因为 openEuler 24.03-LTS-SP4 仓库服务的 HTTP/2 协议层间歇性中断（`Curl error (92): Stream error in the HTTP/2 framing layer, INTERNAL_ERROR`），涉及 `gcc`、`gcc-gfortran`、`glibc-devel`、`guile` 等多个 RPM 包下载失败。该问题与 PR #2992 新增的 Dockerfile 代码无关，Dockerfile 本身语法和逻辑正确。等待仓库服务恢复稳定后重新触发 CI 构建即可。

## 潜在风险
无