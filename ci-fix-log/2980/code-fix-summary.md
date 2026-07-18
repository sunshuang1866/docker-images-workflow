# 修复摘要

## 修复的问题
无需代码修改 — CI 构建过程中 dnf 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时遭遇 HTTP/2 流传输中断（Curl error 92），属于基础设施网络波动问题，与 PR #2980 的代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出本次失败为 infra-error：dnf 解析了全部 258 个依赖包均成功，但在实际下载 cmake-data、git-core、gcc-c++ 等 RPM 包时，openEuler 24.03-LTS-SP4 的 OS 仓库 HTTP/2 连接不稳定，导致 gcc-c++ 经两次镜像重试后仍下载失败。PR #2980 仅新增了 grads 的 Dockerfile 及元数据文件，`dnf install` 命令本身无语法或逻辑错误。修复方案为直接重试 CI 构建。

## 潜在风险
无