# 修复摘要

## 修复的问题
无需代码修复。失败为 CI 基础设施（infra-error）问题。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告确认此为 `infra-error`：aarch64 构建节点在通过 `yum` 从 `repo.openeuler.org` 下载 RPM 依赖包时，遭遇 `repo.openeuler.org` 服务端的 HTTP/2 帧层错误（Curl error 92: `INTERNAL_ERROR`）和 SSL 连接中断（Curl error 56: `SSL_ERROR_SYSCALL`），最终 `vim-common` 包在所有镜像源重试失败后导致 yum 事务中断。

`Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11` 的 `RUN yum install -y ...` 步骤语法正确、依赖声明完整，与 PR 改动无关。这是一个 openEuler 官方仓库的暂时性服务端基础设施问题，不受 PR 代码控制。

建议重新触发 CI 构建（retry），网络恢复后大概率可通过。

## 潜在风险
无