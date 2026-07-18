# 修复摘要

## 修复的问题
CI 构建失败属于基础设施故障（infra-error），无需修改代码。

## 修改的文件
无

## 修复逻辑

根据 CI 失败分析报告，失败原因是 Docker 构建过程中 `dnf install` 从 openEuler 24.03-LTS-SP4 仓库镜像下载 `gcc-c++` 包时，上游镜像服务器反复返回 HTTP/2 帧层流错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），重试耗尽所有镜像后下载失败。同时 `cmake-data` 和 `git-core` 也遭遇同类错误但在重试后成功，说明这是间歇性网络故障。

此问题与本次 PR（#2980）的代码变更无关，PR 仅新增了 Dockerfile 及相关文档文件，`dnf install` 命令格式和依赖包列表均正确。建议等待 openEuler 24.03-LTS-SP4 仓库镜像恢复后重试 CI 构建。

## 潜在风险
无（未修改任何代码）