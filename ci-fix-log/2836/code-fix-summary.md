# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施网络问题（`archive.apache.org` 从 aarch64 runner 不可达），与 PR #2836 代码变更无关。

## 修改的文件
无。

## 修复逻辑
CI 失败分析报告判定失败类型为 `infra-error`，置信度高。Docker 构建时前两个步骤（`yum install java`、`groupadd/useradd`）均成功完成，直到 `Dockerfile:13` 的 `curl` 从 `archive.apache.org` 下载 Apache Cassandra 制品时因网络不可达超时（exit code: 28）。该问题与 PR 新增的 Dockerfile 及配套元数据文件无关，属于 CI runner 节点的网络/防火墙/DNS 配置问题。按照分析报告建议，不应修改 PR 代码，需由 CI 运维团队排查 runner 网络连通性或调整 URL 重写规则。

## 潜在风险
无。未对源码做任何修改。