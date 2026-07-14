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
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: Apache Druid 35.0.0 的二进制包 `apache-druid-35.0.0-bin.tar.gz` 在 `dlcdn.apache.org` 的 CDN 上返回 HTTP 404。与模式01（Apache CDN Maven 版本 404）同根——`dlcdn.apache.org` 是 Apache 的 CDN 分发节点，通常仅保留最新版本或特定版本，不保证历史版本持续可用。

### 与 PR 变更的关联
直接由 PR 变更触发。PR 新增了 Druid 35.0.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile，其中第 9 行的 `wget` 下载 URL `https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 在构建时返回 404。其他变更文件（README.md、doc/image-info.yml、meta.yml）均为元数据/文档更新，不含构建逻辑。

## 修复方向

### 方向 1（置信度: 高）
将 Druid 下载源从 `dlcdn.apache.org` 切换为 `archive.apache.org/dist/druid/`，后者保留所有历史版本的归档制品：

```
https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz
```

这与模式01修复方法 1（换镜像站/归档站）一致。`archive.apache.org` 是 Apache 官方归档站，确保历史版本永久可用。

### 方向 2（置信度: 高）
升级 DRUID VERSION 为 `dlcdn.apache.org` 当前托管的最新版本。如果上游 Apache Druid 已发布新版本（如 35.0.1 或更高），可将 `ARG VERSION` 改为当前 CDN 上实际存在的版本号。

## 需要进一步确认的点
- 确认 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 在 Apache 归档站中确实存在
- 确认 openEuler 24.03-LTS-SP4（`openeuler/openeuler:24.03-lts-sp4`）基础镜像的其他依赖（java-17-openjdk-headless、busybox、iproute、shadow-utils、perl）均可用且版本兼容

## 修复验证要求
修复完成后需验证：
1. 新的下载 URL 在 CI 构建环境中可达且返回 HTTP 200
2. `tar -zxvf` 能成功解压从归档站下载的 tar.gz 包
3. 解压后的目录名与 `mv` 命令中 `apache-druid-${VERSION}` 一致（即 `apache-druid-35.0.0`），确保多阶段构建 COPY 能正确复制文件
