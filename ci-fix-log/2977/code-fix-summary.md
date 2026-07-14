# 修复摘要

## 修复的问题
CI 基础设施错误（infra-error）：`repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库存在 HTTP/2 协议间歇性不稳定问题，导致 `yum install` 下载 `vim-common` 包时 Curl error (92): Stream error in the HTTP/2 framing layer，所有镜像重试耗尽后失败。无需代码修改。

## 修改的文件
无。此失败为临时性网络基础设施问题，与 PR 变更无关，不需要修改任何源文件。

## 修复逻辑
CI 分析报告确认失败类型为 `infra-error`，根因是 `repo.openeuler.org` 仓库服务器的 HTTP/2 协议间歇性不稳定，而非 PR 中 Dockerfile 或任何代码的错误。PR 仅新增了一个标准的 brpc Dockerfile 及三个元数据文件，Dockerfile 中的 `yum install` 命令本身正确无误。在同一构建过程中，`gcc`、`kernel-headers`、`perl-MIME-Base64` 等多个不同大小的包也出现了同类 HTTP/2 流错误（均通过 dnf 重试恢复），进一步证实这是仓库服务端的普遍性问题。应等待仓库服务恢复后重新触发 CI 构建即可。

## 潜在风险
无。