# 修复摘要

## 修复的问题
无需代码修改。该 CI 失败为 `infra-error`（基础设施错误），非代码问题。

## 修改的文件
无。CI 失败与 PR 代码变更无关，无需修改任何文件。

## 修复逻辑
CI 失败发生在 `dnf install` 从 openEuler 24.03-LTS-SP4 官方仓库下载编译依赖包时，仓库镜像站的 HTTP/2 协议层不稳定，导致多个 RPM 包出现 `Curl error (92): Stream error in the HTTP/2 framing layer`。其中 `gcc-c++`（13MB）在多次重试后仍失败，最终所有镜像耗尽。

该失败为 openEuler 镜像站的服务端临时性问题，与 PR #2980 新增的 Dockerfile 及元数据/文档文件无关。任何需要从该仓库下载大量包的 PR 都可能复现此失败。

**推荐操作**：重新触发 CI 构建（如通过 retest 或空 amend commit），大概率能够通过。此问题为偶发性基础设施故障，非代码缺陷。

## 潜在风险
无。