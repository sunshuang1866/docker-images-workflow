# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01
- 新模式标题: (N/A)
- 新模式症状关键词: (N/A)

## 根因分析

### 直接错误
```
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz \
    && tar -zxvf apache-druid-35.0.0-bin.tar.gz \
    && mv apache-druid-35.0.0 /opt/druid \
    && rm -f apache-druid-35.0.0-bin.tar.gz
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget ..." did not complete successfully: exit code: 8
------
Dockerfile:9
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: Apache Druid 35.0.0 的二进制包在 `dlcdn.apache.org` CDN 上已不存在（HTTP 404），与历史模式01（Apache CDN 仅保留最新版本，旧版本下架后 404）完全一致。

### 与 PR 变更的关联
PR 新增了 Druid 35.0.0 的 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`），其中第 9 行直接硬编码了从 `dlcdn.apache.org` 下载的 URL。该 URL 指向 Apache CDN，而 CDN 已不再托管 35.0.0 版本，导致 Docker 构建在 builder 阶段失败。此失败与 PR 代码直接相关。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 切换为 `archive.apache.org/dist/`（Apache 归档站保留所有历史版本），构造正确的下载 URL：
- `https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`
- → `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`

此修复方式与历史模式01、38、02 中的修复思路一致。

### 方向 2（置信度: 中）
如果 `archive.apache.org` 在 CI 构建环境中也不可达（参考模式33中部分 Apache 镜像站网络不通的案例），可使用华为云镜像站或其他已验证可达的镜像源作为替代，前提是该镜像源托管了 Druid 35.0.0 的制品。

## 需要进一步确认的点
- `archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 在 CI 构建环境中的网络可达性（参考模式33，部分 Apache 站点在 CI 中不可达）。
- 如果 archive 站不可达，需确认华为云镜像站 `repo.huaweicloud.com` 或其他镜像源是否托管了 Druid 35.0.0 的二进制包。

## 修复验证要求
code-fixer 在提交前，须通过 `wget --spider` 或等效方式验证新 URL 可正常下载 (HTTP 200)，确保 Apache Druid 35.0.0 的二进制包在所选下载源确实存在且可达。
