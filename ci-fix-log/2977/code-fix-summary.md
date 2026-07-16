# 修复摘要

## 修复的问题
CI 基础设施临时故障，无需代码修复。`yum install` 从 `repo.openeuler.org` 下载 RPM 包时遭遇 HTTP/2 流中断（Curl error 92: INTERNAL_ERROR），`vim-common` 包耗尽重试次数后永久失败。

## 修改的文件
无 — 此为 infra-error，与 PR 代码变更无关。

## 修复逻辑
CI 分析报告指出，失败完全由 `repo.openeuler.org` 软件源在 CI 执行期间的网络波动引发，与 PR #2977 新增的 brpc 24.03-lts-sp4 Dockerfile 及元数据文件无关。同类错误在本次构建中已多次出现（gcc、kernel-headers、perl-MIME-Base64），前三个包经 yum 内置重试后成功恢复。建议在 openEuler 24.03-LTS-SP4 软件源网络状况良好时重新触发 CI 构建（re-run）。

## 潜在风险
无。若后续 CI 反复出现同类问题，需排查 CI aarch64 runner 到 `repo.openeuler.org` 的网络路由，或考虑为该仓库源配置 HTTP/1.1 降级。