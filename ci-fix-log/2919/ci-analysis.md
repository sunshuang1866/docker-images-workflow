# CI 失败分析报告

## 基本信息
- PR: #2919 — chore(spring-boot): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#11 0.080 --2026-07-10 09:28:51--  https://dlcdn.apache.org/maven/maven-3/3.9.12/binaries/apache-maven-3.9.12-bin.tar.gz
#11 0.110 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#11 0.118 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#11 0.128 HTTP request sent, awaiting response... 404 Not Found
#11 0.314 2026-07-10 09:28:51 ERROR 404: Not Found.
#11 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/maven/maven-3/${MAVEN_VERSION}/binaries/apache-maven-${MAVEN_VERSION}-bin.tar.gz      && mkdir -p /usr/local/maven      && tar -zxvf apache-maven-3.9.12-bin.tar.gz -C /usr/local/maven --strip-components=1" did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Others/spring-boot/4.0.2/24.03-lts-sp4/Dockerfile:11`
- 失败原因: `dlcdn.apache.org` 只托管当前最新版 Maven，版本 3.9.12 已被下架，wget 下载返回 HTTP 404

### 与 PR 变更的关联
PR 新增的 Dockerfile (`Others/spring-boot/4.0.2/24.03-lts-sp4/Dockerfile:11`) 中硬编码了从 `dlcdn.apache.org` 下载 Maven 3.9.12 的 wget 命令。该版本在 Apache CDN 已不可用，直接导致 Docker 构建在 builder 阶段的第 3/7 步失败。这是 PR 变更直接触发的失败。

## 修复方向

### 方向 1（置信度: 高）
将 Maven 下载源从 `dlcdn.apache.org` 替换为归档镜像站（如 `archive.apache.org/dist/maven/` 或 `repo.huaweicloud.com/apache/maven/maven-3/`），这些镜像站保留历史版本。修改 Dockerfile 第 11 行的 wget URL，将域名和路径改为归档源对应的格式。

### 方向 2（置信度: 中）
将 `MAVEN_VERSION` 升级到 Apache CDN 当前可用的最新版本（如 3.9.14 或更高），使现有 `dlcdn.apache.org` URL 重新有效。但需注意：Maven 版本变更可能影响 Spring Boot 构建兼容性，需要验证。

## 需要进一步确认的点
- 确认 `archive.apache.org` 或 `repo.huaweicloud.com` 上是否确实存在 Maven 3.9.12 的二进制包
- 确认本仓库中其他使用 `dlcdn.apache.org` 下载 Maven 的 Dockerfile（如 netty 系列）是否也需要同步修复

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用——本次修复不涉及正则 patch 外部源文件）
