# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器被终止
- 新模式症状关键词: graceful_stop, no builder found, closing transport, error reading from server: EOF

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: 无具体代码位置（CI 基础设施层面）
- 失败原因: BuildKit 构建器 `euler_builder_20260709_224657` 在执行 `dnf install` 步骤（下载系统包阶段，耗时约 39 秒）时，BuildKit daemon 发出 `graceful_stop`（GOAWAY），主动终止了构建会话。连接断开后，客户端报 `no builder found`。该错误与 PR 代码变更无关，属于 CI 基础设施层面问题。

### 与 PR 变更的关联
PR 变更仅新增了一个 Dockerfile（安装 gcc、Python 3.9.19 源码编译、pip 安装 scann）和对应的元数据文件。构建在执行 `dnf install` 系统依赖包时被 BuildKit daemon 的优雅关闭所中断。Dockerfile 内容无语法错误或逻辑问题，失败与 PR 代码变更**无关联**。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复**。这是 BuildKit daemon 在构建过程中被主动终止导致的偶发性基础设施故障。建议重新触发 CI 构建（retry），大概率可通过。

## 需要进一步确认的点
- BuildKit daemon 为何在此次构建中发出 `graceful_stop`：可能是 CI runner 节点资源不足、调度器主动回收、或 daemon 进程收到外部信号（如 OOM killer、systemd stop）。
- 若重试后仍失败，需确认 CI runner 节点（`ecs-build-docker-x86-hk`）上 BuildKit daemon 的运行状态和日志。
