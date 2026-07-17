# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器意外关闭
- 新模式症状关键词: graceful_stop, no builder found, rpc error, Unavailable, closing transport, connection error, EOF

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4] RUN dnf install -y ...`（Dockerfile 第 8-10 行对应的 RUN 指令）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 过程中被服务端主动发送 `graceful_stop` goaway 信号后关闭，导致客户端与构建器之间的 gRPC 连接中断（`error reading from server: EOF`），随后构建器实例不可用（`no builder found`）。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准的 Dockerfile（安装 gcc/gcc-c++/make/wget 和 devel 包，构建 Python 3.9.19 并 pip 安装 scann）以及配套的文档/元数据更新。Dockerfile 中 `dnf install` 命令参数正确，包名均合法，构建在 `dnf` 下载元数据阶段（OS metadata 已下载 2.8 MB）被 BuildKit 基础设施中断，而非因代码错误导致。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试。** 此失败属于 CI 基础设施的偶发性故障（BuildKit 构建器被服务端主动关闭），PR 代码变更本身没有问题。直接触发 workflow 重跑（retry）即可，无需修改任何代码。

## 需要进一步确认的点
- 若重试后仍出现相同错误，需排查 BuildKit 构建器 `euler_builder_*` 实例的稳定性：是否存在资源不足（内存/磁盘）、构建器超时回收策略过短、或 `docker-container` driver 的连接保活问题。
