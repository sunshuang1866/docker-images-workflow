# 修复摘要

## 修复的问题
无需代码修改。CI 失败原因为 openEuler 24.03-LTS-SP4 镜像仓库（`repo.****.org`）在下载 RPM 包时发生 HTTP/2 流中断（Curl error 92: INTERNAL_ERROR），属于 CI 基础设施层面的网络 transient 故障，与 PR 代码改动无关。

## 修改的文件
无

## 修复逻辑
- CI 分析报告判定失败类型为 `infra-error`，置信度 **高**。
- 失败发生在 `dnf install` 从外部仓库下载 GCC、glibc-devel 等 RPM 包阶段，多路镜像均出现 HTTP/2 stream 被服务端非正常关闭（`INTERNAL_ERROR (err 2)`）。
- 同一个 CI 构建中 stage-1 镜像（`#7`）和 builder 镜像（`#8`）均遇到相同错误，确认是仓库侧问题而非 PR 专属。
- PR 仅新增了 multiwfn 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及元数据文件，Dockerfile 语法和内容均正确，不涉及任何可触发此故障的代码。
- 按照项目规范中"如果是 infra-error，无需修改代码"的要求，不对任何文件做改动。

## 潜在风险
无