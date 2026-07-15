# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施/网络问题（`infra-error`），CI 构建环境无法连接到 `archive.apache.org:443`，导致 Cassandra 5.0.6 二进制包下载超时。

## 修改的文件
无（infra-error，无需代码修改）

## 修复逻辑
CI 分析报告将本次失败分类为 `infra-error`，根因是 `archive.apache.org` 在 CI 构建环境中不可达（curl exit code 28，TCP 连接超时）。根据修复工程师任务指令：**"如果分析报告指出是 infra-error，在 output_file 中说明无需代码修改，不要强行改代码"**。

本次 PR 为纯增量添加（新增 Cassandra 5.0.6 的 openEuler 24.03-LTS-SP4 Dockerfile），失败与 PR 代码逻辑无关。

## 潜在风险
无代码变更，无风险。

### 后记：建议的修复方向（供 CI 团队参考）
1. **使用华为云镜像站**：将下载源换为 `https://repo.huaweicloud.com/apache/cassandra/${VERSION}/apache-cassandra-${VERSION}-bin.tar.gz`（需先验证镜像站是否托管该文件）。
2. **统一 URL 格式**：SP3 版本的 Dockerfile 使用 `dlcdn.apache.org`，SP4 版本使用 `archive.apache.org`。无论最终选择哪个源，建议保持一致。
3. **排查 URL 重写机制**：CI 日志显示 URL 被从 CDN 地址替换为归档地址，需排查 CI pipeline 中的替换逻辑（Jenkinsfile / 构建脚本 / proxy 配置）。