# 修复摘要

## 修复的问题
无需代码修复。CI 失败为基础设施错误（infra-error），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 构建失败原因是 dnf 从 openEuler 24.03-LTS-SP4 镜像仓库下载 RPM 包时遭遇 HTTP/2 流层错误（Curl error 92: Stream error in the HTTP/2 framing layer），多个包（cmake-data、git-core、gcc-c++）均受影响，gcc-c++ 重试多次后所有镜像均失败。这是 CI 构建节点与 openEuler 镜像仓库之间的网络基础设施问题。

Dockerfile 中 `RUN dnf install -y` 的语法正确，所有包名均有效，PR 新增的文件内容完全正确。建议 CI 触发重试（re-run）即可，无需修改任何代码。

## 潜在风险
无