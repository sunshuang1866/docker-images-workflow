# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施网络瞬态故障（infra-error），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 构建失败由 `repo.openeuler.org` 仓库服务器在构建时段出现 HTTP/2 连接不稳定（Curl error 92: HTTP/2 framing layer INTERNAL_ERROR）和 SSL 传输中断（Curl error 56: SSL_ERROR_SYSCALL）引起。PR 仅新增了一个标准的 brpc Dockerfile，`yum install` 安装的均为 openEuler 24.03-LTS-SP4 官方仓库标准包，Dockerfile 本身无任何问题。触发重试（retrigger CI build）即可。

## 潜在风险
无