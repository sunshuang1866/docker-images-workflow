# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器断连
- 新模式症状关键词: closing transport, connection error, EOF, graceful_stop, no builder found, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建阶段，Dockerfile 第 2/4 步（`dnf install` 下载 metadata 期间）
- 失败原因: BuildKit 构建器 `euler_builder_20260709_224657` 在执行 `dnf install` 的过程中被意外终止（gRPC `graceful_stop`），导致客户端 RPC 连接断开（`connection error: EOF`），后续查询该构建器时返回 `no builder found`。失败与 PR 代码变更无关。

### 与 PR 变更的关联
**无关**。PR 新增的 Dockerfile 内容正确：`dnf install` 安装的包（`gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`）均为 openEuler 24.03-LTS-SP4 标准仓库包，不存在拼写错误或不存在的包名。构建在 `dnf install` 下载 metadata 阶段就因构建器断连而失败，尚未执行到 Python 编译或 pip 安装步骤。失败是 CI 基础设施层面（BuildKit 构建器崩溃/被回收）的问题。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。这是 BuildKit 构建器基础设施故障（构建器进程意外 graceful stop），与 PR 代码无关。Code Fixer 无需修改任何文件，仅需重新触发失败的 job 即可。若重试后仍然失败，再考虑是否为 runner 资源不足（OOM）导致构建器被系统杀死。

## 需要进一步确认的点
- 若重试后仍然在相同位置失败，需检查 Jenkins runner `ecs-build-docker-x86-hk` 的内存/磁盘资源是否充足，`dnf install` 阶段下载 metadata 和安装多个 `-devel` 包可能导致瞬时内存飙升触发 OOM。
- 确认 BuildKit builder `euler_builder_20260709_224657` 的 lifecycle，排除因构建超时或空闲回收策略导致 builder 被提前终止的可能。
