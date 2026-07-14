# 修复摘要

## 修复的问题
无需代码修复。CI 失败由 openEuler 24.03-LTS-SP4 RPM 仓库镜像的 HTTP/2 协议层临时故障（Curl error 92: INTERNAL_ERROR）引起，与本次 PR 的代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告判定失败类型为 `infra-error`，置信度"高"。失败原因是 `dnf install` 在下载大型 RPM 包（gcc、gcc-gfortran 等）时，仓库镜像持续返回 HTTP/2 流错误，导致所有镜像重试耗尽后构建失败。本次 PR 仅新增了 `24.03-lts-sp4/Dockerfile` 及配套元数据，Dockerfile 中 `dnf install` 的语法和包列表均正确。失败完全由外部基础设施问题引起，不属于代码层面的 bug。

## 潜在风险
无。建议等待 openEuler 24.03-LTS-SP4 仓库镜像恢复后重新触发 CI 构建。如果多次重试持续失败，需联系 openEuler 基础设施团队排查镜像站 HTTP/2 配置。