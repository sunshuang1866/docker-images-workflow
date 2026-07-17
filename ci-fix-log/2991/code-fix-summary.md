# 修复摘要

## 修复的问题
无代码修复。CI 失败为 infra-error，根因是 `repo.openeuler.org` 在构建期间 HTTP/2 服务不稳定，导致 `dnf install` 下载 RPM 包时 Curl error 92 (HTTP/2 stream INTERNAL_ERROR)，与本次 PR 代码变更无关。

## 修改的文件
无代码修改。

## 修复逻辑
分析报告指出失败位置在 `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6` 的 `dnf install -y git gcc gcc-c++ make cmake && dnf clean all` 命令。该命令语法完全正确，所请求的包名均存在于 openEuler 24.03-LTS-SP4 仓库中（dnf 已成功解析依赖关系并列出 156 个待安装包）。失败原因是 `repo.openeuler.org` 的 HTTP/2 协议层在构建时间窗口（2026-07-09 14:08 UTC 左右）出现间歇性流中断，属于上游仓库服务端问题。只需等待仓库服务恢复后重新触发 CI 构建即可。

## 潜在风险
无。