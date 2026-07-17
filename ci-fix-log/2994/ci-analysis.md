# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit 构建器被服务端关闭
- 新模式症状关键词: graceful_stop, rpc error, no builder found, closing transport, Unavailable

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`（`dnf install` 下载仓库元数据阶段）
- 失败原因: BuildKit 构建器 `euler_builder_20260709_224657` 被服务端主动发送 `graceful_stop` goaway 信号关闭，导致 RPC 连接中断（`closing transport`），后续步骤无法找到该构建器实例，构建失败。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 及配套的 README、image-info.yml、meta.yml 元数据更新，Dockerfile 内容结构遵循已有的 `24.03-lts-sp3` 模式。构建在早期阶段（`dnf install` 尚未完成元数据下载）即被 BuildKit 服务端关闭打断，未执行到任何由 PR 变更引入的可能出错的步骤。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。此为 CI 基础设施问题——BuildKit 构建器实例在构建过程中被服务端主动关闭（`graceful_stop`）。该错误与代码变更无关，通常由构建节点资源回收、服务端滚动更新、或临时负载均衡策略触发。直接重跑 CI 即可验证 PR 的 Dockerfile 是否能正常通过构建。

## 需要进一步确认的点
- 构建节点 `ecs-build-docker-x86-hk` 在对应时间段的资源使用情况（是否触发了 OOM 或磁盘压力导致的节点驱逐）
- BuildKit 服务端为何对 `euler_builder_20260709_224657` 实例发送 `graceful_stop`——可能是 CI 编排层的超时回收策略或节点维护操作
