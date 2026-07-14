# 修复摘要

## 修复的问题
无需代码修改。CI 失败类型为 `infra-error`，根因是 CI 构建环境无法连接 `archive.apache.org`（IPv4 连接超时、IPv6 网络不可达），导致 wget 下载 Spark 3.4.2 失败。Dockerfile 代码本身正确，此问题与 PR 代码逻辑无关。

## 修改的文件
无（未对任何文件做修改）

## 修复逻辑
分析报告明确指出失败类型为 `infra-error`（置信度: 高），根因是 CI 基础设施网络连通性问题，而非代码缺陷。Dockerfile 中 Spark 下载源 `archive.apache.org` 的 URL 格式与其他 20+ 个同类 Dockerfile（Bigdata/spark/、Bigdata/kyuubi/、Bigdata/livy/ 等）完全一致，代码无错误。CI runner 在当前网络环境下无法访问该域名属于基础设施问题，需要 CI 运维团队排查网络连通性或在 CI 环境中配置代理/镜像。

分析报告虽提供了将下载源切换为 `dlcdn.apache.org` 的修复方向，但根据任务指令中"如果分析报告指出是 infra-error，不要强行改代码"的要求，不对 Dockerfile 做任何代码修改。

## 潜在风险
无（未做任何代码变更）