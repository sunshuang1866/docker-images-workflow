# 修复摘要

## 修复的问题
CI 基础设施临时故障：`repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库在构建时出现 HTTP/2 流传输错误（Curl error 92），导致 `dnf install` 下载 RPM 包失败。此问题与 PR 代码变更无关。

## 修改的文件
无 — 本次 CI 失败为 `infra-error`，PR 代码无需修改。

## 修复逻辑
CI 分析报告明确指出失败原因为 openEuler 24.03-LTS-SP4 aarch64 仓库 `repo.openeuler.org` 的 HTTP/2 服务端临时内部错误（`INTERNAL_ERROR`），多个 RPM 包（git-core、gcc-c++、guile）下载均中断，最终 `guile` 包用尽所有镜像重试后失败。PR 新增的 Dockerfile (`Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`) 的 `dnf install` 命令与仓库中已存在的 SP3 版本完全一致，代码本身没有 bug。

**处理方式**：无需修改任何代码，需重新触发 CI 构建。等待 `repo.openeuler.org` 服务恢复后，重新运行 CI 流水线即可。如果问题持续反复出现，CI 运维需排查 aarch64 仓库节点的 HTTP/2 配置或考虑在 Dockerfile 中为 dnf 增加重试策略作为兜底方案。

## 潜在风险
无 — 未修改任何代码，无风险。