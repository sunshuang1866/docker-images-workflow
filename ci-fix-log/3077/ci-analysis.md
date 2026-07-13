# CI 失败分析报告

## 基本信息
- PR: #3077 — chore(accumulo): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 网络连接超时
- 新模式症状关键词: curl: (28), Failed to connect, Couldn't connect to server, archive.apache.org

## 根因分析

### 直接错误
```
#10 133.8 curl: (28) Failed to connect to archive.apache.org port 443 after 133684 ms: Couldn't connect to server
#10 133.9 tar (child): zookeeper.tar.gz: Cannot open: No such file or directory
#10 133.9 tar (child): Error is not recoverable: exiting now
#10 133.9 tar: Child returned status 2
#10 133.9 tar: Error is not recoverable: exiting now
#10 ERROR: process "/bin/sh -c curl -fSL -o zookeeper.tar.gz https://archive.apache.org/dist/zookeeper/zookeeper-3.9.3/apache-zookeeper-3.9.3-bin.tar.gz; ..." did not complete successfully: exit code: 2
------
Dockerfile:16
  16 | >>> RUN curl -fSL -o zookeeper.tar.gz https://archive.apache.org/dist/zookeeper/zookeeper-3.9.3/apache-zookeeper-3.9.3-bin.tar.gz; \
```

### 根因定位
- 失败位置: `Bigdata/accumulo/3.0.0/24.03-lts-sp4/Dockerfile:16`
- 失败原因: CI 构建环境（aarch64 runner）无法建立到 `archive.apache.org:443` 的 TCP 连接，curl 在约 133 秒后超时（exit code 28），导致 Zookeeper 下载失败。后续 tar 解压报错为级联失败。

### 与 PR 变更的关联
PR 新增了 accumulo 3.0.0 的 openEuler 24.03-LTS-SP4 支持，Dockerfile 第 16 行的 Zookeeper 下载步骤使用了 `archive.apache.org` 作为下载源。该 URL 格式本身正确（与同类 Dockerfile 一致），但 CI 环境的网络出口无法抵达该服务器。这不是 PR 代码逻辑错误，而是 CI 基础设施与远端服务器的网络连通性问题。

此外，日志中还有一个非致命的 yum 镜像警告：
```
[MIRROR] xorg-x11-fonts-others-7.5-27.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/...
```
该警告出现在构建阶段 #9（yum install），但 yum 最终通过其他镜像成功完成安装（日志显示 `Complete!`），并非本次失败的根因。

## 修复方向

### 方向 1（置信度: 高）
将 Zookeeper 下载源从 `archive.apache.org` 切换为 CI 环境网络可达的镜像站（如 `repo.huaweicloud.com/apache/zookeeper/` 或 `mirrors.tuna.tsinghua.edu.cn/apache/zookeeper/`），避免依赖 `archive.apache.org` 的单点网络连通性。

### 方向 2（置信度: 中）
保持 `archive.apache.org` 作为下载源但添加 curl 重试逻辑（`--retry 3 --retry-delay 5`），以应对偶发性网络抖动。但如果 CI 环境与该服务器的网络出口长期不通，此方向无效。

## 需要进一步确认的点
1. 确认 CI aarch64 runner 所在网络是否长期无法访问 `archive.apache.org`（可通过 `curl -v https://archive.apache.org` 在 runner 上手动测试），以判断是临时故障还是长期阻断。
2. 确认同类仓库中其他 Dockerfile（如已有 accumulo 3.0.0-oe2403sp1）使用的 Zookeeper 下载源，以保持一致性。若已有版本使用其他镜像源，新版本应沿用。

## 修复验证要求
若按方向 1 修改下载源，code-fixer 必须在提交前验证新 URL 在 CI runner 网络环境下可达（如通过 curl 测试），确认 `zookeeper-3.9.3` 对应版本的 tar.gz 文件确实存在于目标镜像站路径下。
