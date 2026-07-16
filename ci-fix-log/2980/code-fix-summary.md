# 修复摘要

## 修复的问题
无需代码修复。CI 失败为 infra-error，由 openEuler 24.03-LTS-SP4 官方 RPM 仓库镜像在构建时段出现 HTTP/2 协议层面的间歇性流错误（Curl error 92: INTERNAL_ERROR）导致。

## 修改的文件
无

## 修复逻辑
根据 CI 失败分析报告，失败根因为构建环境中 `dnf install` 从 `repo.****.org` 下载 `gcc-c++`、`cmake-data`、`git-core` 等 RPM 包时遭遇 HTTP/2 流协议错误，其中 `gcc-c++` 包在所有镜像重试耗尽后失败。该错误与 PR #2980 的新增 Dockerfile 及元数据文件变更无关，Dockerfile 中 `dnf install` 命令和包名列表均合法正确。

此为 CI 基础设施网络故障，应等待仓库镜像恢复后重新触发 CI 流水线。

## 潜在风险
无