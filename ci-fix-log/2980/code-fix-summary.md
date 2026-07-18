# 修复摘要

## 修复的问题
CI 基础设施故障（infra-error），无需代码修改。

## 修改的文件
无

## 修复逻辑
CI 失败根因为 openEuler 24.03-LTS-SP4 软件源镜像的 HTTP/2 服务端间歇性不稳定，在下载 `gcc-c++` RPM 包时触发 `Curl error (92): Stream error in the HTTP/2 framing layer`（服务端发送 `INTERNAL_ERROR` RST_STREAM 帧），经多次重试后仍失败导致 `dnf install` 报错。同一次构建中 `cmake-data` 和 `git-core` 两个包也遭遇了相同的 HTTP/2 流错误但最终重试成功，进一步证明为镜像源间歇性故障。

此问题与 PR #2980 的代码变更完全无关。PR 仅新增了一个语法正确、依赖声明合理的 Dockerfile，不涉及任何可能导致下载失败的配置。无需修改任何代码文件，建议触发 CI 重试。

## 潜在风险
无