# 修复摘要

## 修复的问题
无需代码修改 — 此 CI 失败为基础设施问题（infra-error），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败根因为 openEuler 24.03-LTS-SP4 软件仓库的 HTTP/2 流错误（`Curl error (92): Stream error in the HTTP/2 framing layer: INTERNAL_ERROR`），导致部分 RPM 包（`cmake-data`、`git-core`、`gcc-c++`）下载失败。该 Dockerfile 中 `dnf install` 命令语法正确、包名无误，错误发生在从远端仓库下载 RPM 包的网络传输阶段，属于外部仓库服务的瞬时故障。在该 CI 构建中，`cmake-data` 和 `git-core` 重试后成功下载，仅 `gcc-c++` 最终失败，表明重试机制有效。

建议操作：等待仓库服务恢复后重新触发 CI 构建，大概率可自然通过。如果多次重试仍失败，可考虑在 `dnf install` 前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 强制禁用 HTTP/2 降级到 HTTP/1.1。

## 潜在风险
无