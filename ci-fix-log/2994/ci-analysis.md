# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder连接中断
- 新模式症状关键词: rpc error, Unavailable, closing transport, EOF, received prior goaway, graceful_stop, no builder found

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4] RUN dnf install -y ...`（Dockerfile 第 5-7 行）
- 失败原因: BuildKit builder 实例 (`euler_builder_20260709_224657`) 在执行 dnf 包安装过程中被外部因素主动关闭（GOAWAY 帧 debug data: `graceful_stop`），导致客户端与 builder 的 gRPC 连接断开（`error reading from server: EOF`）。builder 消失后，构建系统报告找不到该 builder。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准结构的 Dockerfile（安装系统依赖 → 编译 Python → pip 安装 scann）和配套的 README、image-info.yml、meta.yml 更新。Dockerfile 语法正确，构建步骤无逻辑错误。失败发生在基础的 `dnf install` 系统包安装阶段，属于 CI 基础设施层面的问题（BuildKit builder 进程被外部终止），非代码问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是一个 CI 基础设施故障（BuildKit builder 被环境/系统终止）。应触发 CI 重试（rerun the failed job），大概率能通过。如果重试后仍持续失败，需排查 CI 基础设施：
- 构建节点 `ecs-build-docker-x86-hk` 的 BuildKit 守护进程状态
- 是否有资源限制（内存/OOM）导致 builder 被 kill
- 构建超时配置是否过短（dnf 元数据下载速度仅 77 kB/s，网络可能拥堵）

### 方向 2（置信度: 低）
若重试后同样的 `dnf install` 步骤仍然失败，但错误不同（例如包名不存在、版本冲突等），则可能是 `openssl-devel bzip2-devel zlib-devel` 中有某个包在 openEuler 24.03-LTS-SP4 仓库中名称不同或不存在，需对照 SP4 仓库实际包名进行修正。

## 需要进一步确认的点
- CI 基础设施方确认 `ecs-build-docker-x86-hk` 节点上的 BuildKit daemon 日志，查明 `graceful_stop` 的触发原因（是超时、OOM、还是运维操作）
- 如果该模式在多个 PR 中频繁出现，需评估 BuildKit builder 的生命周期管理策略是否合理
