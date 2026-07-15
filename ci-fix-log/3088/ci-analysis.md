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
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz ...
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`:9
- 失败原因: Apache CDN (`dlcdn.apache.org`) 已下架 Apache Druid 35.0.0 的二进制包，`wget` 下载时返回 HTTP 404。`dlcdn.apache.org` 是 Apache 的 CDN 分发节点，通常只保留最新版本，历史版本下架后不可访问（与模式01中 Maven 的问题同根）。

### 与 PR 变更的关联
PR 新增了 Druid 35.0.0 的 Dockerfile，其中第 9 行 `wget` 命令的下载源直接使用 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`。该 URL 在构建时已返回 404，属于 PR 新增代码直接触发的失败。PR 其余变更（README.md、image-info.yml、meta.yml 的新增条目）与本次失败无关。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org`（仅保留最新版本）更换为 `archive.apache.org`（保留所有历史版本），URL 模板改为：
`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`。

### 方向 2（置信度: 中）
将下载源更换为华为云镜像站（`repo.huaweicloud.com`），该镜像站对 CI 环境兼容性更好且保留历史版本。需确认镜像站中是否存在 `apache/druid/35.0.0/` 路径及对应制品。

## 需要进一步确认的点
- Apache Druid 35.0.0 在 `archive.apache.org/dist/druid/` 下的实际目录结构和文件名是否与预期一致（`apache-druid-35.0.0-bin.tar.gz`）。
- 若换用华为云镜像站，需确认 `repo.huaweicloud.com/apache/druid/35.0.0/` 路径下制品存在且文件名匹配。

## 修复验证要求
code-fixer 必须在修改 Dockerfile 后，手动验证新 URL 可访问（`wget --spider` 或浏览器访问），确认 Apache Druid 35.0.0 制品确实存在于替换后的下载源中，再提交代码。
