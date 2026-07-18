# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器终止
- 新模式症状关键词: graceful_stop, no builder found, closing transport, rpc error, Unavailable

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`（`dnf install` OS 元数据下载阶段）
- 失败原因: BuildKit 远程构建器实例 `euler_builder_20260709_224657` 在 Docker 镜像构建过程中被服务端主动终止（`graceful_stop`），导致客户端收到 GOAWAY 信号后连接断开，构建中断。构建器实例在断开后被移除（`no builder found`）。

### 与 PR 变更的关联
**与 PR 无关。** 本次 PR 新增的 Dockerfile 步骤 `#7`（`dnf install`）是标准操作，日志显示 `dnf` 正在正常下载 OS 元数据（2.8 MB，耗时约 39 秒）时，BuildKit 基础设施发生故障。Dockerfile 本身语法正确，构建定义已被成功加载（`#2 transferring dockerfile: 704B done`）。该失败属于 CI 基础设施层面的 BuildKit 服务端异常终止，非 PR 代码变更触发。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 这是 CI 基础设施问题——BuildKit 构建器实例 `euler_builder_20260709_224657` 在构建中途被服务端终止。应触发 CI 重跑（re-run / retry），若重跑后仍失败，需联系 CI 运维排查 BuildKit 服务端为何发送 `graceful_stop`（可能原因：节点资源不足触发构建器驱逐、构建器实例超时自动回收、宿主机维护操作等）。

## 需要进一步确认的点
- BuildKit 服务端（euler_builder）为何在 `dnf install` 阶段发送 `graceful_stop`：需检查 BuildKit 守护进程日志，确认是资源驱逐、超时策略还是宿主机运维导致。
- 若重试后问题持续出现，需确认 `euler_builder` 构建器池是否存在容量或稳定性问题。
