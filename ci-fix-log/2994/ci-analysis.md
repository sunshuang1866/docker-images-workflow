# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder连接丢失
- 新模式症状关键词: failed to receive status, rpc error, Unavailable, closing transport, EOF, received prior goaway, graceful_stop, no builder found

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`（`dnf install` 安装编译依赖阶段）
- 失败原因: BuildKit 远端 builder 实例 `euler_builder_20260709_224657` 在 Docker 构建过程中发送了 `graceful_stop`（优雅关闭信号），导致 BuildKit 连接被服务端主动断开（`gRPC code: Unavailable`），构建中断。日志显示 `dnf` 正在下载 OS 仓库元数据（2.8 MB，速度仅 77 kB/s，耗时 37 秒）时 builder 失联，极慢的网络速度可能触发了 buildx 服务端的超时/资源回收机制。

### 与 PR 变更的关联
- **与 PR 变更无关**。该 PR 新增了一个完全新的 Dockerfile（`Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`），Dockerfile 语法正确，`dnf install` 中列出的包（`gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`）均为 openEuler 标准仓库包，不存在拼写错误或不存在的包名。
- `dnf` 在下载仓库元数据阶段（尚未开始安装具体包）builder 即断连，说明失败并非由包冲突或 Dockerfile 错误引起。
- 失败发生在 CI 基础设施层（BuildKit builder 连接丢失），不是编译错误、测试失败或依赖问题。

## 修复方向

### 方向 1（置信度: 中）
**触发 CI 重试**。该失败属于 CI 基础设施问题（BuildKit builder 实例被服务端主动断开），与 PR 代码变更无关。重新触发 CI 流水线执行，在新 builder 实例上重新构建即可。如果反复出现同样错误，需联系 CI 基础设施团队排查 buildx builder 实例的稳定性/超时配置。

## 需要进一步确认的点
- BuildKit builder 实例 `euler_builder_20260709_224657` 为何发送 `graceful_stop`：可能是构建超时被杀死，也可能是 CI 资源池回收策略导致。
- `dnf` 元数据下载速度仅 77 kB/s，网络是否异常波动（可能 CI 节点所在网络瞬断触发超时）。
- 同一 PR 的其他架构 job（如 aarch64）是否也出现相同问题，以区分是单节点问题还是 buildx 服务端普遍问题。
