# CI 失败分析报告

## 基本信息
- PR: #3108 — chore(mesos): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式33
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#12 0.085 --2026-07-13 18:25:12--  https://archive.apache.org/dist/mesos/1.11.0/mesos-1.11.0.tar.gz
#12 0.115 Resolving archive.apache.org (archive.apache.org)... 65.108.204.189, 2a01:4f9:1a:a084::2
#12 0.318 Connecting to archive.apache.org (archive.apache.org)|65.108.204.189|:443... failed: Connection timed out.
#12 135.0 Connecting to archive.apache.org (archive.apache.org)|2a01:4f9:1a:a084::2|:443... failed: Network is unreachable.
#12 ERROR: process "/bin/sh -c wget https://archive.apache.org/dist/mesos/${VERSION}/mesos-${VERSION}.tar.gz &&     tar -zxf mesos-${VERSION}.tar.gz" did not complete successfully: exit code: 4
```

### 根因定位
- 失败位置: `Bigdata/mesos/1.11.0/24.03-lts-sp4/Dockerfile`:42（wget 下载 Mesos 步骤）
- 失败原因: CI 构建环境无法与 `archive.apache.org` 建立 TCP 连接（IPv4 Connection timed out，IPv6 Network is unreachable），导致 wget 下载 Mesos 1.11.0 源码包失败（exit code: 4）。该问题与 PR 中已有的两个同类失败（PR #3101 knox、PR #3077 accumulo）完全一致——均为 Apache 镜像站在 CI 环境中网络不可达。

### 与 PR 变更的关联
PR 新增的 Dockerfile 在第 42 行对 Mesos 源码的下载使用了 Apache 下载/归档镜像站地址。该 URL（`archive.apache.org`）在当前 CI 构建网络中不可达，直接导致构建在下载阶段失败。值得注意的是：PR diff 中显示 Dockerfile 使用的是 `downloads.apache.org/mesos/...`，但 CI 日志中实际解析/使用的地址为 `archive.apache.org/dist/mesos/...`（可能存在 DNS CNAME 重定向或 CDN 回源行为），二者最终归于同一不可达域名。

## 修复方向

### 方向 1（置信度: 高）
将 Mesos 源码下载源从 `archive.apache.org`（或 `downloads.apache.org`）替换为已验证在 CI 环境中可达的 Apache 镜像站，例如：
- `dlcdn.apache.org`（Apache CDN，已在 PR #3101 knox 中验证可达）
- `repo.huaweicloud.com`（华为云镜像站，已在 PR #3077 accumulo 中验证可达）

对 URL 路径也需相应调整：`downloads.apache.org/mesos/` → `dlcdn.apache.org/mesos/` 或 `archive.apache.org/dist/mesos/` → `repo.huaweicloud.com/apache/mesos/`。

### 方向 2（可选）
检查 CI 构建节点是否可访问 `archive.apache.org` 的其他备用 IP 地址或是否受临时防火墙/NAT 规则影响。但考虑到已有多次同类历史失败（PR #3101、#3077），此方向为低优先级排查项。

## 需要进一步确认的点
1. 确认 PR diff 中 Dockerfile 的下载 URL（`downloads.apache.org`）与 CI 日志中的实际 URL（`archive.apache.org`）为何不一致——是否存在 DNS CNAME 链或 wget 跟随重定向的行为。
2. 验证 `dlcdn.apache.org/mesos/1.11.0/mesos-1.11.0.tar.gz` 或 `repo.huaweicloud.com/apache/mesos/1.11.0/mesos-1.11.0.tar.gz` 在 CI 构建网络中可达且文件存在。
3. 确认替换后的 URL 在 x86_64 和 aarch64 两个架构的 CI runner 上均可达。

## 修复验证要求
- code-fixer 在修改 Dockerfile 中的下载 URL 后，需确认新 URL 在 CI 环境中可达（可参考 PR #3101 和 PR #3077 已验证通过的镜像站）。
- 验证目标文件 `mesos-1.11.0.tar.gz` 在新镜像站的路径下确实存在且 sha256 与原 Apache 官方发布一致。
- 若使用 `repo.huaweicloud.com`，需确认目录结构 `/apache/mesos/1.11.0/` 下包含正确的 tar.gz 文件。
