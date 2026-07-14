# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01（Apache CDN 404）
- 新模式标题: (不适用)

## 根因分析

### 直接错误
```
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz ...
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz     && tar -zxvf apache-druid-${VERSION}-bin.tar.gz     && mv apache-druid-${VERSION} ${DRUID_HOME}     && rm -f apache-druid-${VERSION}-bin.tar.gz" did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: `dlcdn.apache.org` CDN 不托管 Apache Druid 35.0.0 的二进制包（``https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`` 返回 404），导致 Docker 构建在 wget 步骤失败（exit code: 8）

### 与 PR 变更的关联
PR 新增了 druid 35.0.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile。Dockerfile 第 9 行使用 `dlcdn.apache.org` 作为下载源，该 CDN 仅托管 Apache 项目的最新版本，35.0.0 已从 CDN 下架。这与模式01（Apache CDN Maven 版本 404）的症状高度一致，只是本案例涉及 Druid 而非 Maven。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 替换为 `archive.apache.org`（Apache 归档站），归档站保留历史版本：
- URL 格式参考: `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

### 方向 2（置信度: 中）
若 `archive.apache.org` 同样不可达（参考模式33中 CI 环境对该域名的网络连通性问题），可改用华为云镜像站：
- URL 格式参考: `https://repo.huaweicloud.com/apache/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 需要进一步确认的点
- Apache Druid 35.0.0 是否确实存在正式的 release 制品（需确认 `archive.apache.org/dist/druid/35.0.0/` 目录下文件名格式）。若 35.0.0 本身未发布或制品文件名不同，需进一步核实上游 Apache Druid 的版本发布情况。
- CI 构建环境对 `archive.apache.org` 的网络连通性（历史案例显示部分 CI runner 无法访问该域名，见模式33）。

## 修复验证要求
code-fixer 在提交前，需手动访问 `https://archive.apache.org/dist/druid/35.0.0/` 确认 `apache-druid-35.0.0-bin.tar.gz` 文件确实存在；如不存在，需进一步确认 Druid 35.0.0 的实际发布状态和制品的正确文件名/路径。
