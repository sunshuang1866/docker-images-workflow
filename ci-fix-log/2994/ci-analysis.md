# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器异常终止
- 新模式症状关键词: closing transport, EOF, graceful_stop, no builder found, rpc error, buildkit

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
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`（`dnf install` 下载仓库元数据阶段，已运行约 38 秒）
- 失败原因: BuildKit 构建器 `euler_builder_20260709_224657` 在 Docker 构建过程中异常终止。日志中 `graceful_stop`（goaway code: NO_ERROR）表明构建器守护进程被主动关闭（可能是 CI runner 资源回收、超时触发或节点维护），导致与构建器的 RPC 连接中断，客户端收到 EOF 后无法继续构建，后续查找该 builder 时返回 `no builder found`。

### 与 PR 变更的关联
**无关。** PR 新增的 Dockerfile 本身没有语法错误或逻辑问题——构建在步骤 2/4（`dnf install` 系统依赖）执行到一半时，BuildKit 守护进程被外部终止。这是一个 CI 基础设施层面的故障，并非由 PR 代码变更触发。Dockerfile 中 `dnf install` 的包列表（`gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`）均为 openEuler 仓库中的常规包，不存在导致构建器崩溃的因素。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 这是 BuildKit 构建器被 CI 基础设施意外终止的瞬时故障。无需修改任何文件。在 CI 系统中重新触发该 workflow/job 即可，通常情况下重试后构建器资源正常分配即可通过。若重复出现，需联系 CI 运维排查 runner 节点的 BuildKit daemon 稳定性或资源限制问题。

## 需要进一步确认的点
- 该 job 对应的 x86-64 和 aarch64 两个架构的下游构建 job 是否均为相同失败模式，还是仅某一个架构的 builder 出现问题
- CI runner（`ecs-build-docker-x86-hk`）在对应时间段的资源状况（内存/磁盘/并发构建数），以判断是否是资源耗尽导致的 BuildKit 被 kill
