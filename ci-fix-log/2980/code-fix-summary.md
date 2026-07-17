# 修复摘要

## 修复的问题
无需代码修复。此 CI 失败为基础设施临时故障（infra-error），与 PR 变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败根因是 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）在 dnf 下载 RPM 包时出现 HTTP/2 协议层流错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），多个包（cmake-data、git-core、gcc-c++）受影响，其中 `gcc-c++` 在重试耗尽所有镜像后最终下载失败，导致 Docker 构建退出码为 1。

PR 仅新增了 GrADS 2.2.3 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套文档更新。Dockerfile 中的 `dnf install` 命令语法正确、包列表合理，失败完全源于构建时仓库镜像的 HTTP/2 基础设施临时故障，与 PR 代码变更无关。

**建议操作**：重新触发 CI 构建。如果重试后仍然失败，需联系 openEuler 基础设施团队排查仓库镜像服务的 HTTP/2 代理状态。

## 潜在风险
无