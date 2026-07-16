# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error）：`repo.openeuler.org` 在 aarch64 架构上存在 HTTP/2 传输层间歇性故障（Curl error 92: Stream error in the HTTP/2 framing layer），导致 RPM 包下载失败。

## 修改的文件
无（基础设施故障，无需代码变更）

## 修复逻辑
CI 分析报告将该故障定性为 `infra-error`，置信度：高。失败原因是 `repo.openeuler.org` 的 openEuler-24.03-LTS-SP4 aarch64 仓库在通过 dnf 下载 RPM 包时出现 HTTP/2 流错误，其中 git-core 和 gcc-c++ 经重试后成功，但 guile 包耗尽所有重试次数导致构建失败。该问题与 PR 变更无关，Dockerfile 中的 `dnf install` 命令语法正确，与仓库中其他 openEuler 24.03-lts-sp4 Dockerfile 写法一致。按照修复规范，`infra-error` 不应强行修改代码。建议等待 `repo.openeuler.org` 基础设施恢复后重新触发 CI。

## 潜在风险
无