# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 infra-error，原因是 `repo.openeuler.org` RPM 仓库的 HTTP/2 传输层瞬时故障（Curl error 92 / INTERNAL_ERROR），与 PR #2991 的代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 构建在 `dnf install -y git gcc gcc-c++ make cmake` 阶段失败，原因是 openEuler 官方 RPM 仓库 `repo.openeuler.org` 的 HTTP/2 传输层反复出现流中断，导致 aarch64 架构的 `guile` 等 RPM 包下载失败。PR 仅新增 vvenc 1.14.0 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及相关元数据文件，Dockerfile 中的 `dnf install` 命令语法正确，无任何问题。此失败属于 CI 基础设施侧的瞬时网络问题，建议重新触发 CI（retry）即可。

## 潜在风险
无