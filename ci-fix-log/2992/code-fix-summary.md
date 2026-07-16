# 修复摘要

## 修复的问题
无需代码修改。CI 失败原因为 openEuler 24.03-LTS-SP4 上游 RPM 仓库 HTTP/2 传输层瞬时性故障（Curl error 92: Stream error in the HTTP/2 framing layer），属于 CI 基础设施/上游仓库问题（infra-error），与 PR 代码无关。

## 修改的文件
无

## 修复逻辑
分析报告确认为 infra-error，置信度"高"。builder 阶段的 `dnf install` 在下载 RPM 包时，上游仓库 `repo.****.org` 的 HTTP/2 流未正常关闭（INTERNAL_ERROR），导致 `gcc` 等包经过所有镜像重试后仍下载失败。PR 仅新增了 multiwfn 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套元数据，Dockerfile 语法、包名和构建流程均正确。建议直接重新触发 CI 构建（retry），在仓库网络恢复后应可正常通过。

## 潜在风险
无