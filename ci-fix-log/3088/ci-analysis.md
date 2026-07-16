# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 模式33
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#9 0.350 Connecting to archive.apache.org (archive.apache.org)|65.108.204.189|:443... failed: Connection timed out.
#9 133.8 Connecting to archive.apache.org (archive.apache.org)|2a01:4f9:1a:a084::2|:443... failed: Network is unreachable.
#9 ERROR: process "/bin/sh -c wget https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz     && tar -zxvf apache-druid-${VERSION}-bin.tar.gz     && mv apache-druid-${VERSION} ${DRUID_HOME}     && rm -f apache-druid-${VERSION}-bin.tar.gz" did not complete successfully: exit code: 4
------
Dockerfile:9
--------------------
   8 |
   9 | >>> RUN wget https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz \
  10 | >>>     && tar -zxvf apache-druid-${VERSION}-bin.tar.gz \
  11 | >>>     && mv apache-druid-${VERSION} ${DRUID_HOME} \
  12 | >>>     && rm -f apache-druid-${VERSION}-bin.tar.gz
  13 |
--------------------
ERROR: failed to solve: process "/bin/sh -c wget https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ...
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`（builder 阶段的 wget 下载步骤）
- 失败原因: CI 构建环境中 `archive.apache.org` 无法访问——IPv4 地址 `65.108.204.189:443` 连接超时，IPv6 地址 `2a01:4f9:1a:a084::2:443` 网络不可达，wget 下载 Druid 35.0.0 压缩包失败（exit code: 4）。docker build 中前面的 dnf install 步骤（dnf 从 openEuler 官方仓库安装 java-17、busybox 等）已正常完成，说明 CI 构建节点本身有基础网络能力，但无法连通 `archive.apache.org` 所在的 Apache 基础设施网段。

### 与 PR 变更的关联
PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`（35 行全新文件）、README.md 和 image-info.yml 中的版本条目、meta.yml 中的路径映射。失败直接发生在新增 Dockerfile 的 `wget` 下载步骤——该步骤是 Druid 镜像构建的必经环节，属于本次 PR 引入的新代码触发的失败。

**URL 差异说明**：PR diff 中 Dockerfile 第 9 行写的是 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`，但 CI 日志中实际执行的 URL 是 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`。两种可能的解释：(1) `dlcdn.apache.org` 对非当前版本（druid 35.0.0 可能已被更新的版本替代）进行了 HTTP 302 重定向，将请求透明地转发到 `archive.apache.org`；(2) CI 流水线实际构建的 Dockerfile 与 PR diff 展示的不一致。无论是哪种情况，最终落到的 `archive.apache.org` 在 CI 环境中不可达。

## 修复方向

### 方向 1（置信度: 高）
将 Druid 35.0.0 的下载源从 Apache 官方域名（`dlcdn.apache.org` / `archive.apache.org`）切换为 CI 环境可访问的替代源。根据历史案例（PR #3077、#3101、#3103、#3108），推荐的替代下载源包括：
- **华为云镜像站**：`https://repo.huaweicloud.com/apache/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`
- **清华镜像站**：`https://mirrors.tuna.tsinghua.edu.cn/apache/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

修改 Dockerfile 第 9 行的 wget URL 为上述任一可访问的镜像站地址即可。

### 方向 2（置信度: 低）
如果 Druid 35.0.0 在 `dlcdn.apache.org` 上是可用的（未被重定向到 archive），且当次 CI 失败仅为临时性网络波动，则可以尝试重试构建。但鉴于近期多个 PR（模式 33）均因 `archive.apache.org` 不可达而失败，此方向可能性较低。

## 需要进一步确认的点
1. 确认 `dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 是否确实重定向到 `archive.apache.org/dist/druid/35.0.0/...`（可通过 curl -I 验证），以确定 URL 差异的根因。
2. 确认华为云镜像站 `repo.huaweicloud.com/apache/druid/35.0.0/` 或清华镜像站对应路径下是否存在 Druid 35.0.0 的二进制包，避免选择同样 404 的源。
