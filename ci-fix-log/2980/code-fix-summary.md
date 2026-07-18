# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error）：openEuler 24.03-LTS-SP4 仓库镜像服务器在构建期间发生 HTTP/2 帧层错误，导致 `gcc-c++` RPM 包下载失败。与 PR 代码变更无关。

## 修改的文件
无需代码修改。

## 修复逻辑
根据 CI 失败分析报告，失败类型为 `infra-error`，根因是 `repo.****.org` 仓库镜像服务器的临时 HTTP/2 协议故障（Curl error 92: Stream error in the HTTP/2 framing layer）。该 PR 仅新增了一个标准格式的 Dockerfile，其 `dnf install` 命令语法正确、包名合法，与同仓库中其他版本（如 `24.03-lts-sp3`）的依赖安装方式一致。失败完全由 CI 基础设施的临时网络故障引起，与 PR 代码无关。

**修复方向**：触发 CI 重新构建。等待仓库镜像恢复后重新运行 CI 流水线即可。

## 潜在风险
无