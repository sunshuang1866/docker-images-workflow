# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 意外终止
- 新模式症状关键词: `failed to receive status`, `rpc error`, `closing transport`, `graceful_stop`, `no builder`

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Dockerfile step `[2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`（dnf 下载仓库元数据阶段）
- 失败原因: CI 的 BuildKit builder 实例（`euler_builder_20260709_224657`）在 dnf 安装依赖过程中被意外终止。gRPC 层收到了服务端的 `graceful_stop` GOAWAY 帧，随后连接断开，构建进程无法继续下发 build 指令。这属于 CI 基础设施层面的问题，与 Dockerfile 内容或 PR 改动无关。

### 与 PR 变更的关联
PR 改动（新增 Dockerfile、更新 README / image-info.yml / meta.yml）与本次失败**无直接关联**。Dockerfile 中的 `dnf install` 命令语法正确，失败发生在 CI BuildKit builder 被意外终止的瞬间，而非 dnf 命令执行出错。该 Dockerfile 本身不存在编译错误、依赖缺失或语法问题。

## 修复方向

### 方向 1（置信度: 中）
**触发 CI 重试重新构建**。本次失败为 BuildKit 基础设施临时故障（builder 意外终止），不是代码问题。可尝试 re-run 该 job，大概率能通过。

### 方向 2（置信度: 低）
如果重试后仍失败，检查 CI runner 的资源配额（内存 / 磁盘 / inotify 限制）。`dnf install` 下载 2.8 MB OS 元数据 + 后续安装大量编译工具可能触发 builder 容器的 OOM 或磁盘压力，导致 BuildKit daemon 被 kill。但这点在当前日志中**证据不足**，仅为推测。

## 需要进一步确认的点
1. 重新触发 CI 后，是否在同一位置（dnf install 步骤）再次失败？若反复失败，需获取 BuildKit daemon 端日志（`docker logs euler_builder_*`）以确认终止原因。
2. CI runner 节点（`ecs-build-docker-x86-hk`）在该时间段是否有资源异常或调度器主动驱逐 builder 容器的记录。
3. 是否需要为 `dnf install` 步骤增加 retry 机制（如 `dnf install -y --setopt=retries=5 ...`）以应对偶发的网络/基础设施抖动。
