# 修复摘要

## 修复的问题
CI 构建失败为基础设施问题（infra-error），无需代码修改。

## 修改的文件
无。CI 失败原因与 PR 代码变更无关。

## 修复逻辑
CI 日志显示构建节点（`ecs-build-docker-aarch64-04-sp`）在 `yum install` 过程中从 `repo.openeuler.org` 下载 RPM 包时，遭遇多次 HTTP/2 协议层流错误（Curl error 92）和 SSL 读取系统调用失败（Curl error 56），导致多个软件包（gcc、kernel-headers、perl-MIME-Base64、vim-common）下载失败，最终 yum 安装步骤退出。这些错误是 CI 构建节点到上游镜像源之间的瞬时网络故障，属于 CI 基础设施问题，与 PR 中新增的 Dockerfile 内容无关。Dockerfile 中的 `yum install` 命令格式正确、软件包名规范。建议直接重新触发 CI 构建（`/retest`）即可。

## 潜在风险
无。若多次重试后仍失败，需排查 CI aarch64 runner 到 `repo.openeuler.org` 的出网连通性（防火墙、代理、DNS 或网络质量）。