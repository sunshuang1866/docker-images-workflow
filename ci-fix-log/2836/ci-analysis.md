# CI 失败分析报告

## 基本信息
- PR: #2836 — chore(cassandra): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式33
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#9 [4/5] RUN curl -o /tmp/cassandra-5.0.6.tar.gz https://archive.apache.org/dist/cassandra/5.0.6/apache-cassandra-5.0.6-bin.tar.gz && ...
#9 0.097   % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
#9 0.097                                  Dload  Upload   Total   Spent    Left  Speed
...（约 134 秒全部为 0 字节传输）...
#9 134.4 curl: (28) Failed to connect to archive.apache.org port 443 after 134353 ms: Couldn't connect to server
#9 ERROR: process "/bin/sh -c ..." did not complete successfully: exit code: 28
------
Dockerfile:13
--------------------
  13 | >>> RUN curl -o /tmp/cassandra-${VERSION}.tar.gz https://archive.apache.org/dist/cassandra/${VERSION}/apache-cassandra-${VERSION}-bin.tar.gz && \
  14 | >>>     tar -zxvf /tmp/cassandra-${VERSION}.tar.gz -C /tmp && \
  15 | >>>     cd /tmp/apache-cassandra-${VERSION}/bin && \
  16 | >>>     rm -rf /tmp/cassandra-${VERSION}.tar.gz
```

### 根因定位
- 失败位置: `Database/cassandra/5.0.6/24.03-lts-sp4/Dockerfile:13`（curl 下载 Cassandra 步骤）
- 失败原因: CI 构建环境无法与 `archive.apache.org:443` 建立 TCP 连接，curl 在约 134 秒后超时返回 exit code 28。前序步骤（yum 安装 java、groupadd/useradd）均执行成功。

### 与 PR 变更的关联
PR 新增了 `Database/cassandra/5.0.6/24.03-lts-sp4/Dockerfile`（新文件），这是 CI 中本次失败的唯一构建目标。值得注意的是，**PR Dockerfile 中定义的下载源是 `dlcdn.apache.org`**，而 CI 日志中实际执行的 curl 命令使用了 `archive.apache.org`——两者不一致：

| 来源 | 下载 URL |
|------|---------|
| PR diff（Dockerfile 原文） | `https://dlcdn.apache.org/cassandra/${VERSION}/apache-cassandra-${VERSION}-bin.tar.gz` |
| CI 日志（实际执行） | `https://archive.apache.org/dist/cassandra/5.0.6/apache-cassandra-5.0.6-bin.tar.gz` |

URL 差异说明 CI 构建环境可能对 Apache 下载 URL 进行了替换/代理重写，将 `dlcdn.apache.org` 请求定向到 `archive.apache.org`，而 `archive.apache.org` 从该 CI runner（aarch64）不可达。这与知识库中**模式33**完全吻合——多个历史案例均因 `archive.apache.org` 网络不可达导致 Docker 构建失败。

## 修复方向

### 方向 1（置信度: 中）
将 Cassandra 下载源从 Apache 官方 CDN/归档站替换为华为云镜像站或清华镜像站。参考历史案例 PR #3101、#3077、#3108、#3103 的修复方式，使用 `repo.huaweicloud.com/apache/cassandra/` 或 `mirrors.tuna.tsinghua.edu.cn/apache/cassandra/` 作为下载源。这些镜像站在 CI 环境中已被验证可达。

注意：即使 PR 原文已使用 `dlcdn.apache.org`，CI 对该域名的隐式重写仍可能导致流量被导向 `archive.apache.org`。直接用非 Apache 域名（华为云/清华镜像站）可完全绕过 CI 的 URL 重写机制。

### 方向 2（置信度: 低）
确认 CI 系统中是否存在 URL 代理或重写规则（将 `dlcdn.apache.org` 映射到 `archive.apache.org`）。如果这是 CI 基础设施层面的配置错误，修复 CI 配置本身即可，无需修改 Dockerfile。

## 需要进一步确认的点
1. **URL 替换机制**：需要确认 CI 构建环境是否有机房级代理/URL 重写规则将 `dlcdn.apache.org` 的请求透明转发到 `archive.apache.org`。如果存在此类规则，可考虑在 CI 配置中将重写目标改为华为云或清华镜像站。
2. **dlcdn.apache.org 在 CI 环境中的实际可达性**：如果直接测试 `dlcdn.apache.org` 在该 CI runner 上可达，说明问题出在 URL 重写层而非网络层，此时无需修改 Dockerfile 下载源。
3. **其他架构 runner 的构建结果**：日志只展示了 aarch64 构建过程，需确认 x86_64 runner 是否也遇到同样的网络连接问题。

## 修复验证要求
- code-fixer 修改 Dockerfile 下载源后，需确认 CI 构建环境实际执行的 URL 不再指向 `archive.apache.org`。可通过 CI 日志中 curl 命令的实际 URL 来验证。
- 如果修复方向选为"换华为云镜像站"，需先在浏览器或 CI runner 上手动验证 `https://repo.huaweicloud.com/apache/cassandra/5.0.6/apache-cassandra-5.0.6-bin.tar.gz` 是否返回 HTTP 200，确认华为云镜像站确实托管了 Cassandra 5.0.6 的二进制包。
