# 修复摘要

## 修复的问题
CI 构建失败，`dnf install` 从 `repo.openeuler.org` 下载 aarch64 RPM 包时出现 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），属于 CI 基础设施/网络层面故障，与 PR 代码无关。

## 修改的文件
无。CI 失败为 `infra-error`，无需修改任何代码文件。

## 修复逻辑
CI 失败分析报告判定失败类型为 `infra-error`，根因位于 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 软件仓库在 HTTP/2 传输中多次出现服务端 `INTERNAL_ERROR`，导致多个 aarch64 RPM 包下载失败。这不是 PR 新增的 vvenc Dockerfile 或任何代码变更引入的问题。任何在同一时刻从该仓库下载 aarch64 包的构建都会遇到相同错误。**无需代码修改，重新触发 CI 构建有较大概率通过。**

若问题持续出现，可考虑在 Dockerfile 的 `dnf install` 前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 将 dnf/libcurl 回退到 HTTP/1.1 作为临时绕过方案，但此为服务端问题的工作绕过（workaround），不应作为长期修复方案。

## 潜在风险
无 —— 未修改任何代码。