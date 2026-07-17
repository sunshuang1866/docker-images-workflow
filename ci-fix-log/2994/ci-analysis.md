# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit builder 连接中断
- 新模式症状关键词: failed to receive status, rpc error, closing transport, graceful_stop, no builder found, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`（`RUN dnf install` 下载 OS 元数据时），非代码文件行
- 失败原因: CI 的 Docker BuildKit builder 实例 `euler_builder_20260709_224657` 在执行构建过程中被服务端主动关闭（`graceful_stop`），导致 gRPC 传输连接中断，后续查找该 builder 时报 `no builder found`。这是 CI 基础设施层面的问题，与 PR 代码变更无关。

### 与 PR 变更的关联
**无关。** PR #2994 仅新增了 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 及配套的 README.md、doc/image-info.yml、meta.yml 更新。失败发生在 Docker 构建的 `dnf install` 阶段（安装标准系统包 gcc、openssl-devel 等），此时尚未执行任何与 scann 或 Python 编译相关的操作。BuildKit builder 被优雅关闭（`graceful_stop`）是 CI runner / builder 节点管理层面的行为，PR 的代码变更不会触发 builder 关闭。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 由于失败原因为 CI 基础设施的 BuildKit builder 在中途被关闭，PR 代码本身无问题，重新触发 CI job 即可。无需修改任何代码或 Dockerfile。

## 需要进一步确认的点
- 如果重试后仍然在同一位置失败（`dnf install` 下载元数据阶段 builder 被关闭），需排查 CI 的 builder 节点资源是否不足、是否存在定时回收 builder 的策略，以及 `euler_builder` 的生命周期管理机制。
- 确认 builder 被 `graceful_stop` 的具体原因（是否为节点缩容、维护、超时自动回收等）。
