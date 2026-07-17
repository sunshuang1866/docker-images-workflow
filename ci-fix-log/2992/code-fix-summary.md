# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 openEuler 24.03-LTS-SP4 软件仓库服务器的 HTTP/2 协议间歇性流错误（Curl error 92），属于基础设施问题（infra-error），非 PR 代码缺陷。

## 修改的文件
无（infra-error，无需代码修改）

## 修复逻辑
CI 分析报告明确指出：失败类型为 `infra-error`，根因是 openEuler 24.03-LTS-SP4 的 DNF 软件仓库在通过 HTTP/2 协议下载 RPM 包时反复出现 `Stream error in the HTTP/2 framing layer`（Curl 错误码 92），多次重试后耗尽所有镜像导致 `dnf install` 失败。

PR #2992 新增的 Dockerfile 内容正确无语法错误，`dnf install` 命令中列出的包名均有效（与 SP3 版本一致）。该问题可通过以下方式规避（非代码修改）：
- **重试构建**：该问题表现为间歇性，重新触发 CI 构建可能通过。
- **DNF 配置降级到 HTTP/1.1**：在 Dockerfile 的 `dnf install` 前添加 `RUN echo "http2=false" >> /etc/dnf/dnf.conf` 以规避 HTTP/2 流错误。
- **增加 DNF 重试次数**：在 `dnf install` 命令中添加 `--setopt=retries=10` 提高重试次数。

按照修复原则，`infra-error` 不应强行修改代码。

## 潜在风险
无