# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error），无需代码修改。

## 修改的文件
无

## 修复逻辑
CI 失败的原因是 `repo.openeuler.org` 在 aarch64 runner 上构建时 HTTP/2 传输层反复出现流错误（`Curl error 92: Stream error in the HTTP/2 framing layer`），导致 `git-core`、`gcc-c++`、`guile` 等多个 RPM 包下载失败。这是上游仓库在构建窗口内的瞬时网络/HTTP/2 服务异常，与 PR 的 Dockerfile 及元数据文件变更完全无关。

PR 的 Dockerfile（`Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`）内容正确，`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all` 安装命令本身没有问题。应在 CI 侧重试该 job，或等待仓库服务恢复后重新触发构建。

## 潜在风险
无