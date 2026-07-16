# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 被终止
- 新模式症状关键词: graceful_stop, closing transport, no builder found, rpc error: code = Unavailable

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
- 失败位置: Docker BuildKit builder `euler_builder_20260709_224657`（x86-64 runner `ecs-build-docker-x86-hk`），Docker 构建步骤 `[2/4]` 执行 `dnf install` 时
- 失败原因: BuildKit builder 实例在构建进行中被外部触发优雅关闭（`graceful_stop`），导致 gRPC 连接断开，Docker 构建的客户端无法从 builder 接收状态，随后 builder 实例已被销毁（`no builder "euler_builder_20260709_224657" found`），构建失败

### 与 PR 变更的关联
**与 PR 变更无关。** 此次 PR 仅新增了 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 及配套的 README、meta.yml、image-info.yml 更新。构建在 `dnf install` 阶段失败，该命令是该仓库中数百个 Dockerfile 的标准写法，不存在语法或逻辑错误。失败的直接原因是 CI 基础设施中 BuildKit builder 进程被异常终止，属于 infra-error。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 此为 CI 基础设施问题，BuildKit builder 实例在构建过程中被意外关闭。建议：
- 确认构建节点 `ecs-build-docker-x86-hk` 在构建时段是否有维护操作或资源回收事件
- 重新触发 CI 流水线（retrigger），大概率重新构建即可通过

## 需要进一步确认的点
- BuildKit builder `euler_builder_20260709_224657` 被优雅关闭的原因（是否有资源配额限制、节点维护计划、或 builder 进程的存活探针超时）
- 该 runner 节点的 dnf 下载速度极低（77 kB/s，2.8 MB 用时 37 秒），是否存在网络波动或镜像源问题导致构建时间过长、触发超时回收
