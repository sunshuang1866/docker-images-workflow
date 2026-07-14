# CI 失败分析报告

## 基本信息
- PR: #2944 — chore(activemq): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: ActiveMQ 下载源 404
- 新模式症状关键词: dlcdn.apache.org, 404 Not Found, activemq, wget, exit code: 8

## 根因分析

### 直接错误
```
#10 [5/6] RUN wget https://dlcdn.apache.org//activemq/${VERSION}/apache-activemq-${VERSION}-bin.tar.gz ...
#10 0.056 --2026-07-09 13:18:05--  https://dlcdn.apache.org//activemq/6.1.7/apache-activemq-6.1.7-bin.tar.gz
#10 0.085 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#10 0.086 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#10 0.097 HTTP request sent, awaiting response... 404 Not Found
#10 0.295 2026-07-09 13:18:06 ERROR 404: Not Found.
#10 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org//activemq/${VERSION}/apache-activemq-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Others/activemq/6.1.7/24.03-lts-sp4/Dockerfile:28`
- 失败原因: Dockerfile 中 ActiveMQ 6.1.7 的下载源 `dlcdn.apache.org/activemq/6.1.7/apache-activemq-6.1.7-bin.tar.gz` 返回 HTTP 404。`dlcdn.apache.org` 是 Apache 的 CDN 分发节点，通常只保留最新版本，不保证历史版本的可用性（与模式01中 Maven 的问题同根）。此外，URL 中存在双斜杠拼写错误（`//activemq`），虽非 404 的直接原因，但属规范性瑕疵。

### 与 PR 变更的关联
PR 新增了 ActiveMQ 6.1.7 在 openEuler 24.03-LTS-SP4 上的 Dockerfile。该 Dockerfile 是从已有 SP2 版本复制并修改而来的全新文件。失败由 Dockerfile 中硬编码的下载 URL 指向了 CDN 上已下架/不存在的制品导致，与 PR 的代码变更直接相关。

## 修复方向

### 方向 1（置信度: 高）
将 ActiveMQ 下载源从 `dlcdn.apache.org` 更换为 `archive.apache.org/dist/activemq/`。Apache Archive 永久保留所有历史版本，不会因版本迭代而移除旧版制品。同时修正 URL 中的双斜杠拼写（`//activemq` → `/dist/activemq`）。

参考 URL 格式：`https://archive.apache.org/dist/activemq/${VERSION}/apache-activemq-${VERSION}-bin.tar.gz`

### 方向 2（置信度: 中）
如果 `archive.apache.org` 在 CI 构建环境中不可达（参考模式33），可改用华为云镜像站：`https://repo.huaweicloud.com/apache/activemq/${VERSION}/apache-activemq-${VERSION}-bin.tar.gz`。需确认 CI 构建环境能访问该镜像站。

## 需要进一步确认的点
- 确认 `archive.apache.org/dist/activemq/6.1.7/` 路径下确实存在 `apache-activemq-6.1.7-bin.tar.gz` 文件
- 确认同版本（6.1.7）的已有 Dockerfile（SP1、SP2）使用的下载源是否为同一 URL；如果是，它们可能也需要一并修复（或已通过其他渠道缓存/绕过）
- 确认 CI 构建环境能否正常访问 `archive.apache.org`

## 修复验证要求
code-fixer 在修改下载 URL 后，应以 `wget --spider` 或等价方式验证新 URL 能成功返回 HTTP 200，而非 404 或连接超时：
- 验证 `https://archive.apache.org/dist/activemq/6.1.7/apache-activemq-6.1.7-bin.tar.gz` 可达
- 若 archive 不可达，验证华为云镜像站替代 URL 可达
