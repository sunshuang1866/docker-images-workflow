# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error），无需代码修改。

## 修改的文件
无

## 修复逻辑
CI 失败由 openEuler 24.03-LTS-SP4 官方仓库 `repo.openeuler.org` 在 aarch64 runner 上的 HTTP/2 流错误（Curl error 92）导致。多个包（git-core、gcc-c++、guile）下载时 HTTP/2 连接异常中断，其中 `guile` 包重试耗尽全部镜像后导致 `dnf install` 整体失败。该问题与 PR #2991 的变更无关 — Dockerfile 中的 `dnf install` 命令格式与项目中大量其他 Dockerfile 完全一致，属于上游仓库的瞬时网络故障。分析报告建议重试 CI 构建即可通过，不需要修改任何代码。

## 潜在风险
无