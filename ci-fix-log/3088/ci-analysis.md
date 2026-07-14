# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01

## 根因分析

### 直接错误
```
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`（`RUN wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`）
- 失败原因: Apache CDN（`dlcdn.apache.org`）已下架 Druid 35.0.0 的二进制包，返回 HTTP 404，导致 wget 下载失败（exit code: 8）。这与模式01（Apache CDN Maven 版本 404）的症状一致：`dlcdn.apache.org` 仅保留最新版本制品，历史版本会被移除。

### 与 PR 变更的关联
**直接关联**。PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其中下载源使用了 `dlcdn.apache.org`。该 URL 在 PR 提交时可能有效（同版本 35.0.0 的 SP2 Dockerfile 此前构建成功），但 CDN 已清理该版本制品，导致此次 CI 构建时 404。PR 选择了不稳定的 CDN 下载源是失败的直接原因。

## 修复方向

### 方向 1（置信度: 高）
将 Druid 下载源从 `dlcdn.apache.org` 切换为 Apache 归档站 `archive.apache.org`，该站保留所有历史版本且模式01中已验证有效。修改 Dockerfile 第 9 行，将下载 URL 从：
```
https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz
```
改为：
```
https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz
```

### 方向 2（置信度: 中）
如果 `archive.apache.org` 同样不可达（参考模式33中 `archive.apache.org` 在 CI 环境中可能网络不通），可改用华为云镜像站 `repo.huaweicloud.com` 的 Apache 镜像路径。

## 需要进一步确认的点
- 确认 `archive.apache.org/dist/druid/35.0.0/` 路径下确实存在 `apache-druid-35.0.0-bin.tar.gz` 文件，且文件名格式与 Dockerfile 中的变量展开一致。
- 确认 CI 构建环境能正常访问 `archive.apache.org`（该域名在模式33中有网络不通的历史案例，若不可达则需走方向2）。

## 修复验证要求
code-fixer 必须验证 `https://archive.apache.org/dist/druid/35.0.0/` 目录下实际存在的文件名与 Dockerfile 中 `${VERSION}` 变量展开后的文件名 `apache-druid-35.0.0-bin.tar.gz` 完全一致。如 archive.apache.org 在 CI 环境中不可达，需进一步验证 `repo.huaweicloud.com` 是否提供 Druid 35.0.0 的镜像。
