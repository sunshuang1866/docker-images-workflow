# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式（与模式01高度同类——Apache CDN 404）
- 新模式标题: CDN 不托管 Druid 制品
- 新模式症状关键词: dlcdn.apache.org, 404 Not Found, wget, exit code: 8, apache-druid

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
   9 | >>> RUN wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz \
------
ERROR: failed to solve: process "/bin/sh -c wget ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`（builder 阶段的 `wget` 步骤）
- 失败原因: `dlcdn.apache.org` CDN 对 Druid 35.0.0 的下载请求返回 HTTP 404，该 CDN 可能不托管 Druid 项目或已移除该版本

### 与 PR 变更的关联
**直接关联**——PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`（全新文件），其中下载 URL 写为 `dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`（VERSION=35.0.0）。该 URL 在 Apache CDN 上不存在（404），这是本次 PR 引入的唯一构建错误。`stage-1` 阶段（安装 `java-17-openjdk-headless`、`busybox`、`shadow-utils`、`perl` 等依赖）本身被 CANCELED，因为 builder 阶段先失败导致整个构建中止，这些 RPM 安装步骤本身没有问题。

## 修复方向

### 方向 1（置信度: 高）
将 Druid 35.0.0 的下载源从 `dlcdn.apache.org` 更换为 `archive.apache.org/dist/druid/`（Apache 归档站，保留所有历史版本），URL 格式变为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`。该类修复与历史模式01（Apache CDN Maven 404）同根，`archive.apache.org` 是已验证可用的替代源。

### 方向 2（置信度: 中）
若 `archive.apache.org` 不可达（参考模式33中该域名的网络超时问题），可改用华为云镜像站 `https://repo.huaweicloud.com/apache/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`，该镜像站已在模式01/33中多次验证可达。

## 需要进一步确认的点
1. **验证 Druid 35.0.0 在 `archive.apache.org` 的实际路径和文件名**：确认 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 确实存在且可下载。
2. **参考同仓库已有 SP2 Dockerfile**：`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile` 中使用的下载源 URL 格式应作为修复的直接参考，SP2 版本应已有可正常工作的下载 URL。
3. **Dockerfile 第3行的小写 `as` 问题**：日志中出现警告 `FromAsCasing: 'as' and 'FROM' keywords' casing do not match (line 3)`，Dockerfile 中 `FROM ${BASE} as builder` 的 `as` 为小写，而 `FROM` 为大写，建议统一为大写 `AS` 以消除构建警告（非致命，不影响构建）。

## 修复验证要求
code-fixer 必须在提交前执行以下验证步骤：
1. 从 `archive.apache.org/dist/druid/35.0.0/` 确认 `apache-druid-35.0.0-bin.tar.gz` 文件存在且可正常下载（非 404）。
2. 若 archive.apache.org 不可达，需验证华为云镜像站 `repo.huaweicloud.com/apache/druid/35.0.0/` 上该文件的可用性。
3. 确认选用下载源后，`wget` 命令能成功获取文件且 `tar -zxvf` 可正常解压。
