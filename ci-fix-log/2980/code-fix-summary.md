# 修复摘要

## 修复的问题
无需代码修改。CI 失败由 openEuler 24.03-LTS-SP4 RPM 仓库镜像 HTTP/2 传输中断导致（Curl error 92），属于 CI 基础设施瞬时网络故障，与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告确认此失败为 `infra-error`，根因是 `https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/` 仓库镜像在 HTTP/2 协议传输过程中发生流中断，多个 RPM 包（cmake-data、git-core、gcc-c++）下载失败。PR 仅新增了 GrADS 2.2.3 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及元数据文件，Dockerfile 中 `dnf install` 包列表语法正确、包名有效。**无需对任何代码文件做修改**，直接重试 CI 构建即可。

## 潜在风险
若重试后仍然失败，需由 CI 运维团队排查 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 服务端配置或网络链路稳定性。