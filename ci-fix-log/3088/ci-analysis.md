# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz ...
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
------
Dockerfile:9
--------------------
   8 |     
   9 | >>> RUN wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz \
  10 | >>>     && tar -zxvf apache-druid-${VERSION}-bin.tar.gz \
  11 | >>>     && mv apache-druid-${VERSION} ${DRUID_HOME} \
  12 | >>>     && rm -f apache-druid-${VERSION}-bin.tar.gz
  13 |     
--------------------
ERROR: failed to solve: process "/bin/sh -c ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: `dlcdn.apache.org` CDN 上 `druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 404。Apache CDN（`dlcdn.apache.org`）通常仅保留最新版本，旧版本下架后即返回 404（与模式01中 Maven 的问题同根）。

### 与 PR 变更的关联
PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其中硬编码了从 `dlcdn.apache.org` 下载 Druid 35.0.0 的 URL。这是 PR 直接引入的失败——该下载 URL 在 `dlcdn.apache.org` 上不可用（404）。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 更换为 Apache 归档站 `archive.apache.org/dist/druid/`，归档站保留所有历史版本，不受 CDN 清理策略影响。URL 格式参考：`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`。

### 方向 2（置信度: 中）
检查 Apache Druid 35.0.0 在 `dlcdn.apache.org` 上的实际命名格式。下载文件名可能与预期不同（如 `apache-druid-${VERSION}-bin.tar.gz` 与实际 CDN 上的文件名不完全一致，或目录路径格式有变体）。可手动访问 `https://dlcdn.apache.org/druid/` 确认实际目录和文件命名。

## 需要进一步确认的点
- 需要验证 `archive.apache.org/dist/druid/35.0.0/` 路径下是否存在 `apache-druid-35.0.0-bin.tar.gz`（确认归档站确实保留了该版本）
- 需要确认 `archive.apache.org` 在 CI 构建环境中网络可达（参考模式33，`archive.apache.org` 在部分 CI 环境中可能不可达）
- 如果 `archive.apache.org` 也不可达，可尝试使用华为云镜像站 `repo.huaweicloud.com/apache/druid/` 作为替代下载源

## 修复验证要求
若修复方向涉及将下载源更换为 `archive.apache.org`，code-fixer 必须在提交前执行以下验证：
1. 手动访问 `https://archive.apache.org/dist/druid/35.0.0/` 确认该版本确实存在于归档站
2. 确认归档站上该版本的文件名与 Dockerfile 中构造的 `${VERSION}` 变量展开后的文件名一致
3. 若 `archive.apache.org` 不可达，需验证华为云镜像站或其他替代源的可用性
