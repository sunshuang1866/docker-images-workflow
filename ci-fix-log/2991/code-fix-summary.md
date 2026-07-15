# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error）：`repo.openeuler.org` 在 aarch64 架构上对 openEuler 24.03-LTS-SP4 仓库的 HTTP/2 传输层间歇性故障（Curl error 92），导致 `dnf install` 下载 RPM 包失败。与 PR 代码变更无关，无需修改代码。

## 修改的文件
无。

## 修复逻辑
CI 失败根因是上游镜像站 `repo.openeuler.org` 的 HTTP/2 实现不稳定，在 `dnf install` 下载 `git-core`、`gcc-c++`、`guile` 等 aarch64 RPM 包时反复出现 `INTERNAL_ERROR` 流错误，最终耗尽所有镜像源后退出。PR 中 `Dockerfile:6` 的 `dnf install -y git gcc gcc-c++ make cmake` 命令语法正确、包名有效，不属于代码缺陷。

建议操作：重新触发 CI 构建，等待镜像站恢复后应能正常通过。若重试后仍持续失败，可考虑在 Dockerfile 的 `dnf install` 前添加 `dnf makecache` 和 `/etc/dnf/dnf.conf` 中的 `retries=5` / `timeout=30` 配置以提高容错能力。

## 潜在风险
无。