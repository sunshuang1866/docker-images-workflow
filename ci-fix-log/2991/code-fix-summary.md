# 修复摘要

## 修复的问题
无需代码修改 — CI 失败为基础设施问题（infra-error）。

## 修改的文件
无

## 修复逻辑
CI 分析报告指出失败类型为 `infra-error`，置信度高。失败原因是 CI 构建环境（aarch64 runner）在执行 `dnf install` 从 `repo.openeuler.org` 下载 RPM 包时，多个包（git-core、gcc-c++、guile）遭遇 HTTP/2 流错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），`guile` 包耗尽所有镜像重试后下载失败。

PR 变更仅新增了一个标准格式的 Dockerfile（`Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`），其 `dnf install` 命令与同类已有 Dockerfile 完全相同，仅基础镜像版本从 `sp3` 变为 `sp4`。失败完全由 `repo.openeuler.org` 的 HTTP/2 CDN 节点临时性问题导致，与 PR 代码变更无关。

**建议操作**：等待网络恢复后重新触发 CI 构建。

## 潜在风险
无