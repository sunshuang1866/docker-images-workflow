# 修复摘要

## 修复的问题
无需代码修改。CI 失败由 `repo.openeuler.org` 在 aarch64 架构上的 HTTP/2 协议层异常（Curl error 92: INTERNAL_ERROR）导致，属 CI 基础设施层面的网络问题，与 PR 代码改动无关。

## 修改的文件
无

## 修复逻辑
失败类型为 **infra-error**。Dockerfile 中 `RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all` 命令为标准合法写法，openEuler 官方仓库 `repo.openeuler.org` 的 aarch64 频道在构建时段出现 HTTP/2 流错误，导致多个 RPM 包下载失败。这不是代码问题，而是源仓库服务端的间歇性网络故障。建议在仓库恢复后重新触发 CI 流水线即可通过。

## 潜在风险
无