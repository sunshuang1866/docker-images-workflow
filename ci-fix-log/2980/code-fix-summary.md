# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施故障（infra-error）：构建过程中 openEuler 24.03-LTS-SP4 软件仓库镜像站的 HTTP/2 连接不稳定，导致 `cmake-data`、`git-core`、`gcc-c++` 等 RPM 包下载失败（Curl error 92: Stream error in the HTTP/2 framing layer）。

## 修改的文件
无

## 修复逻辑
根据 CI 失败分析报告的诊断，失败类型为 **infra-error**，根因是 openEuler 软件仓库镜像站的临时网络故障，与 PR #2980 新增的 Dockerfile 代码无关。Dockerfile 语法正确，`dnf install` 中列出的软件包均存在于 openEuler 24.03-LTS-SP4 仓库中。修复方式是重新触发 CI 构建，无需对代码做任何修改。

## 潜在风险
无