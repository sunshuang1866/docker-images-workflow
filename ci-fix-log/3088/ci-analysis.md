# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01（变体）
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
------
Dockerfile:9
--------------------
   9 | >>> RUN wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz \
  10 | >>>     && tar -zxvf apache-druid-${VERSION}-bin.tar.gz \
  11 | >>>     && mv apache-druid-${VERSION} ${DRUID_HOME} \
  12 | >>>     && rm -f apache-druid-${VERSION}-bin.tar.gz
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: Apache Druid 35.0.0 的二进制包在 CDN 节点 `dlcdn.apache.org` 上不存在（HTTP 404）。该 CDN 通常仅保留最新版本，历史版本会被下架。

### 与 PR 变更的关联
PR 新增了 Druid 35.0.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile，其中第 9 行硬编码使用 `dlcdn.apache.org` 作为下载源。该 CDN 已不再托管 Druid 35.0.0 版本的二进制包，导致 Docker 构建在下载阶段立即失败。PR 改动直接触发了该失败——上传到 CDN 可用的下载源就不会有问题。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 更换为 `archive.apache.org`，Apache Archive 长期保留历史版本：

```
wget https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz
```

若 `archive.apache.org` 在 CI 环境中不可达（参考模式33），则可换用已证可达的镜像站（如 `repo.huaweicloud.com/apache/druid/`）。

## 需要进一步确认的点
- 需要确认 `35.0.0-oe2403sp2` 的 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）是否使用相同 URL 且当前构建正常。若 SP2 也使用 `dlcdn.apache.org` 且构建正常，说明 CDN 可能在最近才移除该版本，SP2 需要同步修复。
- 需要验证 `archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 或镜像站对应路径确实存在该文件。

## 修复验证要求
code-fixer 必须确认替换后的下载 URL（如 `archive.apache.org/dist/druid/35.0.0/` 或 `repo.huaweicloud.com/apache/druid/35.0.0/`）在提交前可访问且能返回 HTTP 200 及完整二进制包，不可仅凭路径规则推断 URL 正确性。
