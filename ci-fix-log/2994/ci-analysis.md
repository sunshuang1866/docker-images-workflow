# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 优雅断连
- 新模式症状关键词: gracefiul_stop, goaway, NO_ERROR, no builder found, rpc error, closing transport, docker-container driver

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`（`RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`），具体在 dnf 下载包阶段（约 38 秒后）
- 失败原因: BuildKit 远端 builder 实例 `euler_builder_20260709_224657` 在 Docker 构建过程中被服务端主动优雅关闭（goaway: `graceful_stop`, code: `NO_ERROR`），导致当前构建上下文中的 gRPC 连接断开，BuildKit 客户端无法继续接收构建状态。这不是构建代码本身的错误，而是 CI 基础设施 builder 生命周期管理问题。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了 scann 1.4.2 在 openEuler 24.03-lts-sp4 上的 Dockerfile（21 行）及相关元数据文件（README.md、image-info.yml、meta.yml）。构建在非常早期的 `dnf install` 阶段就因 builder 服务端断连而中止，并未到达任何可能与 PR 改动相关的代码或安装逻辑。RFC goaway `graceful_stop` + `NO_ERROR` 明确表明这是 builder 平台侧发起的主动连接终止，不是由 Dockerfile 指令错误触发的。

## 修复方向

### 方向 1（置信度: 中）
**重试构建**。此为 CI 基础设施 builder 实例被动回收导致的瞬断故障，Dockerfile 本身不存在代码问题。重新触发 CI job 大概率可以通过。

## 需要进一步确认的点
1. 如果重试后仍然在同一阶段失败，需检查 BuildKit builder 池的闲置超时回收策略：`euler_builder_20260709_224657` 是否因上游 trigger 编排层耗时过长（日志显示从流水线启动到实际开始构建中间有较长的 `splitter` / `eulerpublisher` 预处理阶段）超过了 builder keep-alive 时间而被服务端回收。
2. 检查 dnf 下载速度（77 kB/s，2.8 MB 耗时 37 秒）是否显著低于正常水平，如有必要排查 CI runner 网络出口带宽或 openEuler 仓库源可达性。
