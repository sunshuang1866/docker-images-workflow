# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Builder被优雅关闭
- 新模式症状关键词: graceful_stop, closing transport, error reading from server: EOF, no builder found

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 [2/4]（`dnf install` 执行中）
- 失败原因: CI 的 BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 过程中被外部信号优雅关闭（`graceful_stop`），导致 gRPC 连接断开（`error reading from server: EOF`），客户端失去与构建器的通信，后续再次查找该构建器时已不存在。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 内容语法正确，`dnf install` 步骤中列出的所有包（gcc、gcc-c++、make、wget、openssl-devel、bzip2-devel、zlib-devel）均为 openEuler 仓库中的标准包。构建失败发生在 `dnf` 下载元数据的阶段（`38.59 OS` 表示正在进行仓库元数据同步），而非包安装或包名错误阶段。构建器被 `graceful_stop` 信号终止是基础设施层面的问题。

## 修复方向

### 方向 1（置信度: 高）
**Code Fixer 无需处理。** 这是一个 CI 基础设施故障（构建器被异常回收/超时），与 PR 代码内容无关。建议：
- 重新触发 CI 运行（retry/rebuild）
- 如果反复出现，联系 CI 基础设施团队排查构建器 `ecs-build-docker-x86-hk` 节点的资源状况和超时策略

## 需要进一步确认的点
- 当前提供的日志仅为 x86-64 架构构建 job 的日志。如果 aarch64 架构的构建 job 同样失败，需要获取其日志以确认是否为相同的基础设施问题还是另有其他原因。
- 构建器 `euler_builder_20260709_224657` 被 `graceful_stop` 的具体原因（是否触发了 CI 平台的超时限制、内存/磁盘资源限制，或是节点被调度回收）。
