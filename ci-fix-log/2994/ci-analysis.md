# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit builder 被关闭
- 新模式症状关键词: failed to receive status, rpc error, graceful_stop, no builder found, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker build 步骤 `#7 [2/4]`，dnf 正在下载包元数据时
- 失败原因: CI 的 Docker BuildKit builder 实例 `euler_builder_20260709_224657` 在构建过程中被服务端主动关闭（`graceful_stop`），导致 buildx 客户端与 builder 之间的 gRPC 连接断开，构建中断。

### 与 PR 变更的关联
**与 PR 代码变更无关**。本次 PR 仅新增了一个 Dockerfile（`Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`）、更新了 README.md、doc/image-info.yml 和 meta.yml 四个文件，均为常规的镜像版本新增操作。构建在执行到 dnf install 阶段（即新增 Dockerfile 的第 2 个 RUN 指令）时，BuildKit builder 服务端主动发送了 `graceful_stop` goaway 信号并关闭连接，属于 CI 基础设施的调度/资源回收问题。

## 修复方向

### 方向 1（置信度: 高）
重新触发 CI 运行。BuildKit builder 因服务端 `graceful_stop` 被提前销毁属于 CI 基础设施的偶发性问题（例如 builder 实例到达生命周期上限、集群资源回收、或调度器重调度），与本次 PR 的代码变更无关。重试 CI 构建即可。

## 需要进一步确认的点
- Builder 实例 `euler_builder_20260709_224657` 被 `graceful_stop` 的具体原因（资源配额耗尽、节点排水、定时回收策略等），需查询 CI 集群的 BuildKit builder 管理策略。
- 如果多次重试均在同一 builder 或同一阶段失败，需检查 CI 平台 BuildKit 服务端是否存在稳定性问题。
