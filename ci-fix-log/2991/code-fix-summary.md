# 修复摘要

## 修复的问题
无需代码修改。CI 失败原因为 openEuler 24.03-LTS-SP4 aarch64 仓库（`repo.openeuler.org`）的 HTTP/2 协议层临时基础设施问题，与 PR 代码变更无关。

## 修改的文件
无。该失败为 `infra-error`，不需要修改任何源代码文件。

## 修复逻辑
CI 构建在 `aarch64` runner 上执行 `dnf install -y git gcc gcc-c++ make cmake` 时，多个 RPM 包（`git-core`、`gcc-c++`、`guile`）在下载过程中遇到 HTTP/2 帧层流错误（Curl error 92: INTERNAL_ERROR），最终 `guile` 包耗尽所有镜像源导致安装失败。Dockerfile 中的 `dnf install` 命令语法正确，所列包名均为 openEuler 仓库中存在的标准包。此为仓库服务端的临时性网络问题，触发 CI 重试即可通过。

## 潜在风险
无