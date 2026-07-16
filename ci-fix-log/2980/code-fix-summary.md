# 修复摘要

## 修复的问题
CI 构建失败由 openEuler 24.03-LTS-SP4 官方仓库镜像的临时性 HTTP/2 协议错误（Curl error 92）导致，与 PR 代码变更无关。无需代码修改。

## 修改的文件
无。该失败属于 infra-error，不需要修改任何源代码。

## 修复逻辑
CI 分析报告明确指出：失败发生在 `dnf install` 阶段下载 RPM 包时，`repo.openeuler.org` 镜像服务器返回 HTTP/2 流协议错误（`INTERNAL_ERROR`），导致 `gcc-c++` 等大包下载失败。该错误：

1. 与本次 PR 新增的 Dockerfile 及元数据文件内容**完全无关**——Dockerfile 的包名、依赖清单均正确；
2. 属于上游镜像仓库的**基础设施层间歇性故障**，非代码缺陷；
3. 同一 CI 运行中 `cmake-data` 和 `git-core` 也曾遇到相同错误但经重试后成功，仅 `gcc-c++` 两次重试均失败。

建议操作：重新触发 CI 构建。若多次重试后仍然失败，需联系 openEuler 镜像仓库运维排查 HTTP/2 服务端问题。

## 潜在风险
无（未修改任何代码）。