# 修复摘要

## 修复的问题
无需代码修改。CI 失败由基础设施问题导致：构建节点无法通过 HTTPS(443) 连接到 `downloads.apache.org` 的所有解析 IP（IPv4 超时 + IPv6 不可达），属于 CI 网络层面的连通性故障。

## 修改的文件
无

## 修复逻辑
- 分析报告明确分类为 `infra-error`，根因是 CI 构建节点到 `downloads.apache.org` 的网络路由不通，与 PR 代码变更无关。
- 同一构建中 `dlcdn.apache.org`（Hadoop 下载）连通正常，说明是特定主机/网段被阻断，而非 PR 代码问题。
- 按照流程规范，`infra-error` 类型不应强制修改代码来绕过基础设施问题。

**建议的后续操作**：
1. 在 CI runner 上手动验证 `downloads.apache.org` 的可达性（`curl -v https://downloads.apache.org/knox/2.1.0/knox-2.1.0.zip`）。
2. 若持续不可达，可考虑将下载源更换为 `https://archive.apache.org/dist/knox/${VERSION}/knox-${VERSION}.zip`（Apache Archive 归档站），作为补充修复方向。
3. 重试 CI 构建，排除临时性网络波动。

## 潜在风险
无（未修改任何代码）