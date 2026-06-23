# CI 失败分析报告

## 基本信息
- PR: #2704 — 【自动升级】kylin容器镜像升级至5.0.3版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: GitHub Release URL 404
- 新模式症状关键词: curl: (22), 404, github.com, releases/download, apache kylin

## 根因分析

### 直接错误
```
#24 [18/25] RUN mkdir -p /home/kylin/apache-kylin-5.0.3-bin && \
    curl -fSL -o apache-kylin.tar.gz \
    https://github.com/apache/kylin/releases/download/kylin-5.0.3/apache-kylin-5.0.3-bin.tar.gz && \
    tar -zxf apache-kylin.tar.gz -C /home/kylin/apache-kylin-5.0.3-bin --strip-components=1 && \
    rm -rf apache-kylin.tar.gz
#24 0.079   % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
#24 0.080                                  Dload  Upload   Total   Spent    Left  Speed
#24 0.080   0     9    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
#24 0.185 curl: (22) The requested URL returned error: 404
#24 ERROR: process "/bin/sh -c ..." did not complete successfully: exit code: 22
------
Dockerfile:60
------
ERROR: failed to solve: process "/bin/sh -c ..." did not complete successfully: exit code: 22
```

### 根因定位
- 失败位置: `Bigdata/kylin/5.0.3/24.03-lts-sp3/Dockerfile:60-63`
- 失败原因: Dockerfile 中构造的 GitHub Release 下载 URL `https://github.com/apache/kylin/releases/download/kylin-5.0.3/apache-kylin-5.0.3-bin.tar.gz` 不存在（HTTP 404），可能的原因包括：① Apache Kylin 5.0.3 尚未在该 URL 发布 release 制品；② GitHub Release 的 tag 命名格式不是 `kylin-${VERSION}`（例如可能是 `v5.0.3` 或 `5.0.3`）；③ 制品文件名与预期不一致。

### 与 PR 变更的关联
PR 新增了完整的 Kylin 5.0.3 Dockerfile（83 行全新文件），此即触发失败的直接变更。Dockerfile 第 60-63 行的 `curl` 命令从 GitHub 下载 Kylin 5.0.3 二进制包时，目标 URL 不存在，导致 Docker 构建在步骤 18/25 失败。

## 修复方向

### 方向 1（置信度: 高）
确认 Apache Kylin 5.0.3 在 GitHub Releases 的实际 tag 名称和制品文件名。访问 `https://github.com/apache/kylin/releases` 或 `https://github.com/apache/kylin/releases/tag/kylin-5.0.3`，确认：
- release tag 是否为 `kylin-5.0.3` 或其他格式（如 `v5.0.3`）；
- 制品文件的实际名称（如 `apache-kylin-5.0.3-bin.tar.gz` 是否存在，或后缀为 `.tar.gz`、`.tgz` 等变体）；
- 修正 Dockerfile 中的 URL 以匹配实际可用的 release 地址。

### 方向 2（置信度: 中）
如果 Apache Kylin 5.0.3 的 GitHub Release 确实不存在或不完整，考虑改用 Apache 官方归档源 `https://archive.apache.org/dist/kylin/` 或 `https://dlcdn.apache.org/kylin/` 下载，参考 Kylin 官方下载页面获取正确 URL。

## 需要进一步确认的点
1. 在 `https://github.com/apache/kylin/releases` 页面上确认 kylin-5.0.3 release 是否存在，以及其实际 tag 名和制品文件名。
2. 如果 GitHub Release 不存在，确认 Apache Kylin 5.0.3 是否通过官方 ASF 发布渠道（`https://kylin.apache.org/download/` 或 `https://archive.apache.org/dist/kylin/`）提供二进制包。
3. 确认制品文件名中 `-bin` 后缀是否为该版本的标准命名（部分 Kylin 版本制品可能不使用 `-bin` 后缀）。
4. 附带观察：`conf/hadoop/hadoop-env.sh` 中 `JAVA_HOME` 指向 `/usr/lib/jvm/java-8-openjdk-amd64`，而 Dockerfile 中 `JAVA_HOME` 设为 `/usr/lib/jvm/java-1.8.0-openjdk`，两者不一致——在 openEuler 上安装 `java-1.8.0-openjdk-devel` 后实际路径需确认，当前失败与此无关但可能影响运行时。

## 修复验证要求
code-fixer 在修改 Dockerfile 中的 download URL 前，必须通过 `curl -I` 或 `wget --spider` 验证新的 URL 可访问（返回 HTTP 200），确保修正后的 URL 确实能下载到 Apache Kylin 5.0.3 版本的正确二进制包。
