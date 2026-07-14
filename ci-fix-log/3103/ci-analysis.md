# CI 失败分析报告

## 基本信息
- PR: #3103 — chore(kyuubi): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式33、模式09（叠加）

## 根因分析

### 直接错误
```
#8 [builder 3/5] RUN wget https://downloads.apache.org/kyuubi/kyuubi-1.11.1/apache-kyuubi-1.11.1-bin.tgz && ...
#8 0.220 Connecting to downloads.apache.org (downloads.apache.org)|95.216.224.44|:443... failed: Connection timed out.
#8 135.2 Connecting to downloads.apache.org (downloads.apache.org)|88.99.208.237|:443... failed: Connection timed out.
#8 270.4 Connecting to downloads.apache.org (downloads.apache.org)|2a01:4f8:10a:39da::2|:443... failed: Network is unreachable.
#8 270.4 Connecting to downloads.apache.org (downloads.apache.org)|2a01:4f9:2b:1cc2::2|:443... failed: Network is unreachable.
#8 ERROR: process "/bin/sh -c wget https://downloads.apache.org/kyuubi/kyuubi-${KYUUBI_VERSION}/apache-kyuubi-${KYUUBI_VERSION}-bin.tgz && ..." did not complete successfully: exit code: 4
```

### 根因定位
- 失败位置: `Bigdata/kyuubi/1.11.1/24.03-lts-sp4/Dockerfile:17`（Kyuubi 下载步骤）
- 失败原因: CI aarch64 构建环境（`ecs-build-docker-aarch64-01-sp`）无法与 `downloads.apache.org` 建立 TCP 连接，所有 IPv4 地址均 Connection timed out，IPv6 地址 Network is unreachable，wget 退出码 4

### 与 PR 变更的关联
PR 新增的 Dockerfile 使用 `https://downloads.apache.org/kyuubi/...` 作为 Kyuubi 下载源，该域名在 CI aarch64 runner 构建环境中网络不可达。**该问题与 PR 代码逻辑无关**，系 CI 基础设施网络限制所致，但可通过换用其他下载源在 Dockerfile 层面绕过。

此外，Dockerfile 第 29-35 行的 JDK 下载步骤中使用了 `BUILDARCH` 变量（BuildKit 预定义全局 ARG），在 `RUN` 中对其重新赋值不会生效（**模式09**）。当前构建在 Kyuubi 下载阶段即失败，未触发该问题，但修复网络问题后 JDK 下载步骤将因 `BUILDARCH` 变量冲突而导致架构字符串错误、产生 404——这个问题在 PR #2105 中已为 SP3 版本修复过。

## 修复方向

### 方向 1（置信度: 高）
将 Kyuubi 下载源从 `downloads.apache.org` 切换为 `dlcdn.apache.org`（或其他 CI 环境可访问的镜像源，如 `archive.apache.org/dist/kyuubi/`），参考模式33历史案例（PR #3101 Knox、PR #3108 Mesos）。

### 方向 2（置信度: 高）
将 JDK 下载步骤中的 `BUILDARCH` 变量重命名为自定义名称（如 `JAVA_ARCH`），避免与 BuildKit 预定义变量冲突，参考模式09历史案例（PR #2105 曾为 Kyuubi SP3 修复同类问题）。

## 需要进一步确认的点
1. 确认 `dlcdn.apache.org` 或 `archive.apache.org` 在 CI aarch64 runner 上可以正常访问（通过查看同类仓库其他成功构建的镜像所使用的 Apache 下载域名确认）
2. 确认 `https://dlcdn.apache.org/kyuubi/kyuubi-1.11.1/apache-kyuubi-1.11.1-bin.tgz` 路径下的制品确实存在（非 404）

## 修复验证要求
- code-fixer 必须确认所选替代下载源（如 `dlcdn.apache.org`）上确有 Kyuubi 1.11.1 对应制品，再行提交
- code-fixer 必须确认 `BUILDARCH` 重命名后，JDK 下载 URL 中的架构字符串（`x64` / `aarch64`）构造正确，且在 aarch64 runner 上 JDK 下载 URL 返回 200 而非 404
