# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01 / 模式38
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
ERROR: failed to solve: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: Apache Druid 35.0.0 已从 `dlcdn.apache.org` CDN 中下架（CDN 仅保留最新版本），`wget` 下载该版本二进制包时返回 HTTP 404

### 与 PR 变更的关联
PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其中 builder 阶段的 wget 命令使用 `dlcdn.apache.org` 作为下载源。Apache CDN（`dlcdn.apache.org`）只托管当前最新版本，Druid 35.0.0 已不是最新版本，因此被 CDN 移除，导致 404。此问题与历史模式01（Apache CDN Maven 版本 404）和模式38（ActiveMQ 下载源 404）完全同根——均为 `dlcdn.apache.org` 不保留历史版本所致。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 切换为 `archive.apache.org`，Apache Archive 保留了所有历史版本的归档制品。URL 模板为：
```
https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz
```
这是处理 `dlcdn.apache.org` 历史版本 404 的标准修复方式，与模式01、模式38 一致。

### 方向 2（置信度: 中）
若 Apache Archive 也不可用，可考虑使用华为云镜像站等国内镜像源作为替代下载源。

## 需要进一步确认的点
- 确认 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 确实存在且可被 CI 构建环境访问
- 确认 Druid 35.0.0 是否为当前最新版本——如有更新的 patch 版本，也可以考虑升级版本号来规避此问题

## 修复验证要求
code-fixer 必须从浏览器或 curl 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 可正常下载（HTTP 200），确认归档路径和文件名均正确后再修改 Dockerfile 并提交。
