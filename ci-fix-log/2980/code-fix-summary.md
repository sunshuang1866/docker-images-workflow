# 修复摘要

## 修复的问题
CI 基础设施/网络瞬态故障：openEuler 24.03-LTS-SP4 仓库镜像 HTTP/2 流错误导致 `gcc-c++` 等 RPM 包下载失败，触发 dnf install 构建失败。与 PR 代码变更无关。

## 修改的文件
无代码修改。

## 修复逻辑
该失败为 **infra-error**（类型确认于 CI 分析报告），根因是 CI 构建环境从 `repo.****.org` 下载 RPM 包时，多个包遭遇 `Curl error (92): Stream error in the HTTP/2 framing layer`。`cmake-data` 和 `git-core` 在重试后成功，但 `gcc-c++`（13 MB 大包）两次遭遇 HTTP/2 流错误后耗尽所有 mirror 重试次数。该错误是 openEuler 仓库镜像服务器或中间网络代理的 HTTP/2 协议层瞬态故障，与 PR 新增的 Dockerfile 及元数据文件无关。建议直接重试 CI 构建，通常 2-3 次重试后可通过。若持续复现，需排查仓库镜像 HTTP/2 服务端健康状况或 CI 节点网络代理配置。

## 潜在风险
无。