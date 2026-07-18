# 修复摘要

## 修复的问题
infra-error：openEuler 24.03-LTS-SP4 仓库镜像服务器 HTTP/2 协议层瞬时故障导致 RPM 包下载失败。无需代码修改。

## 修改的文件
无。该失败为 CI 基础设施/网络问题，与 PR 代码变更无关。

## 修复逻辑
CI 构建过程中，`dnf install` 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包（cmake-data、git-core、gcc-c++）时，镜像服务器多次返回 HTTP/2 协议层流错误（Curl error 92: `Stream error in the HTTP/2 framing layer`, `INTERNAL_ERROR`）。其中 cmake-data 和 git-core 在重试后成功下载，但 gcc-c++（13 MB）两次重试均失败并耗尽所有镜像重试次数。

Dockerfile 本身的 `dnf install` 命令写法与同类 Dockerfile 一致，没有语法错误或依赖包名问题。该失败属于 openEuler 仓库镜像服务器的瞬时性网络故障，与 PR 新增的 Dockerfile 代码无关。

**建议操作**：重新触发 CI 构建。该问题为间歇性网络故障，重试大概率会成功（其他受影响的包在重试后均成功下载）。

## 潜在风险
无。