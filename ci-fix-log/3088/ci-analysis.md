# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01
- 新模式标题: (无)
- 新模式症状关键词: (无)

## 根因分析

### 直接错误
```
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz ...
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process ... did not complete successfully: exit code: 8
------
Dockerfile:9
   9 | >>> RUN wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz \
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: `dlcdn.apache.org` 仅托管 Apache 各项目的最新版本，Druid 35.0.0 已从 CDN 下架，下载 URL 返回 HTTP 404（与知识库模式01中 Maven 版本 404 及模式38中 ActiveMQ 版本 404 同根）。

### 与 PR 变更的关联
PR #3088 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其中第 9 行 `wget` 的目标 URL 指向 `dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`，该文件在当前时间点已不在 CDN 上，导致构建必然失败。失败由 PR 变更直接触发。

## 修复方向

### 方向 1（置信度: 高）
将 Dockerfile 中下载源从 `dlcdn.apache.org` 切换为 `archive.apache.org`，后者保留所有历史版本：
- 将 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`
- 替换为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

### 方向 2（置信度: 中）
若 `archive.apache.org` 在 CI 环境中网络不可达（参考知识库模式33中多个同类案例），可使用华为云镜像站 `repo.huaweicloud.com/apache/druid/` 作为替代下载源。

## 需要进一步确认的点
1. 确认 Druid 35.0.0 在 `archive.apache.org/dist/druid/35.0.0/` 路径下确实存在该二进制包。
2. 确认 CI 构建环境能够正常访问 `archive.apache.org`（需注意模式33中部分 CI 实例无法连接 `archive.apache.org` 的情况，备选方案为 `repo.huaweicloud.com`）。

## 修复验证要求
code-fixer 必须通过 `wget --spider https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`（或同等手段）先在浏览器/本地环境中确认修复后的 URL 可访问且返回 HTTP 200，再提交代码。若 archive 不可达，验证 `https://repo.huaweicloud.com/apache/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 可用性后替换。
