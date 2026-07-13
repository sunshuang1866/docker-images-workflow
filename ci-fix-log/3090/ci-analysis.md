# CI 失败分析报告

## 基本信息
- PR: #3090 — chore(flink): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 模式01（变种）
- 新模式标题: (不适用 — 匹配已有模式)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#12 0.056 + wget -nv -O flink.tgz https://dlcdn.apache.org/flink/flink-2.1.0/flink-2.1.0-bin-scala_2.12.tgz
#12 0.466 https://dlcdn.apache.org/flink/flink-2.1.0/flink-2.1.0-bin-scala_2.12.tgz:
#12 0.466 2026-07-10 08:26:57 ERROR 404: Not Found.
#12 0.467 + CONF_FILE=/opt/flink/conf/config.yaml
#12 0.467 + /bin/bash /opt/flink/bin/config-parser-utils.sh /opt/flink/conf ...
#12 0.468 /bin/bash: /opt/flink/bin/config-parser-utils.sh: No such file or directory
#12 ERROR: process "/bin/sh -c set -ex &&     wget ... did not complete successfully: exit code: 127
```

### 根因定位
- 失败位置: `Bigdata/flink/2.1.0/24.03-lts-sp4/Dockerfile:38`（RUN set -ex 步骤中的 wget 命令）
- 失败原因: Apache CDN (`dlcdn.apache.org`) 不再托管 Flink 2.1.0 的二进制包，`wget` 下载 URL 返回 HTTP 404。由于 `set -e` 在 `&&` 链中不触发退出，脚本继续执行到 `config-parser-utils.sh`，因 Flink 未解压而报 "No such file or directory"（exit code 127），此为二次连锁错误，非根因。

### 与 PR 变更的关联
PR 变更**未直接引入此错误**：新增的 Dockerfile 使用了与已有 SP1/SP2 Dockerfile 相同的 `VERSION=2.1.0` 和相同的 `dlcdn.apache.org` 下载源。根本原因是 Apache CDN 在已有 SP1/SP2 镜像构建之后移除了 Flink 2.1.0，导致当前 SP4 构建时触发 404。此问题与 PR 的具体改动无关，但 PR 是触发 CI 重新构建的时机点。

## 修复方向

### 方向 1（置信度: 中）
将 Flink 下载源从 `dlcdn.apache.org`（仅托管最新版本）切换为 `archive.apache.org/dist/flink/`（保留所有历史版本）：

- 当前 URL: `https://dlcdn.apache.org/flink/flink-${VERSION}/flink-${VERSION}-bin-scala_2.12.tgz`
- 替换为: `https://archive.apache.org/dist/flink/flink-${VERSION}/flink-${VERSION}-bin-scala_2.12.tgz`

同类的 SP1/SP2 Dockerfile 如需保持一致，也应同步修改。

### 方向 2（置信度: 低）
升级 Flink VERSION 到当前 Apache CDN 上实际可用的最新版本。但此方案需要同步更新 docker-entrypoint.sh 脚本以匹配新版本的启动方式，影响面较大，且可能与上游 Docker 镜像的版本策略不一致。

## 需要进一步确认的点
1. **确认 Flink 2.1.0 在 `archive.apache.org` 确实存在**：访问 `https://archive.apache.org/dist/flink/flink-2.1.0/` 验证该版本是否已在归档站中。如果归档站也没有，则说明 Flink 2.1.0 尚未正式发布或已被完全移除。
2. **确认已有 SP1/SP2 Dockerfile 是否使用相同 URL**：检查 `Bigdata/flink/2.1.0/24.03-lts-sp1/Dockerfile` 和 `Bigdata/flink/2.1.0/24.03-lts-sp2/Dockerfile` 是否同样引用 `dlcdn.apache.org`。如果是，这些 Dockerfile 在重新构建时也会遇到相同的 404，需要一并修复。

## 修复验证要求
code-fixer 必须在确认修复方向前：
1. 验证 `https://archive.apache.org/dist/flink/flink-2.1.0/flink-2.1.0-bin-scala_2.12.tgz` 返回 HTTP 200（而非 404）。
2. 如果归档站也不存在该文件，则需搜索 Apache Flink 官方发布渠道（如 `https://flink.apache.org/downloads/`）确认 Flink 2.1.0 的实际发布状态及可用的下载链接格式。
