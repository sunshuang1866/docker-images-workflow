# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 模式01（Apache CDN 版本 404）+ 模式38（ActiveMQ 下载源 404，同为 dlcdn.apache.org 非 Maven 制品 404）

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
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9-12`（`RUN wget` 步骤）
- 失败原因: `dlcdn.apache.org`（Apache CDN）不保留历史版本制品，Apache Druid 35.0.0 的 binary tarball 已从 CDN 下架（与模式01 中 Maven 版本被移除、模式38 中 ActiveMQ 被移除的机制完全相同）。此前同一版本 35.0.0 的 SP2 Dockerfile 构建时该制品尚在 CDN 上，现已过期被清理。

### 与 PR 变更的关联
**PR 直接触发**。PR 新增的 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`）在第 9 行使用 `dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 作为下载源，该 URL 在 PR 提交时已失效。PR 变更内容本身逻辑正确（版本号、依赖包、目录结构均合理），问题仅在于下载源选择不当。

此外，日志中存在一个非致命 WARN：`FromAsCasing: 'as' and 'FROM' keywords' casing do not match (line 3)`——Dockerfile 第 3 行 `FROM ${BASE} as builder` 中的 `as` 为小写而 `FROM` 为大写，建议修正为 `AS`，但这不是构建失败的原因。

## 修复方向

### 方向 1（置信度: 高）
将 Druid 下载源从 `dlcdn.apache.org`（仅保留最新版本的 CDN）更换为 `archive.apache.org`（Apache 归档站，保留所有历史版本）。参考模式01/02/38 的同类修复方案，将 URL 改为：

`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

这确保 Druid 35.0.0 的制品始终可获取，不随 CDN 版本轮换而失效。同时建议将 `FromAsCasing` 的 `as` 改为 `AS` 以消除 BuildKit 警告。

## 需要进一步确认的点
- 确认 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 确实存在且可访问（archive.apache.org 的路径格式与 dlcdn 可能略有不同，需验证完整 URL）。
- 确认 CI 构建环境的网络能访问 `archive.apache.org`（模式33 记录了部分环境下 `archive.apache.org` 可能不可达；若不可达，备选方案为 `repo.huaweicloud.com/apache/druid/` 或其他华为云镜像站）。
- 确认现有 SP2 的 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）是否也使用 `dlcdn.apache.org` 作为下载源——若使用相同 URL，未来 SP2 构建同样会失败，建议一并修复。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（本修复不涉及正则 patch 外部源文件，无需填写此项。）
