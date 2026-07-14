# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器回收
- 新模式症状关键词: graceful_stop, no builder.*found, closing transport, error reading from server: EOF, rpc error: code = Unavailable

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Dockerfile 第 2 个 RUN 步骤（`dnf install`），但非 Dockerfile 代码问题
- 失败原因: BuildKit 构建器 `euler_builder_20260709_224657` 在 Docker 构建执行中（`[2/4] dnf install` 步骤）被意外终止。日志显示 `debug data: "graceful_stop"`，表明构建器被优雅关闭（回收/缩容/超时），导致 BuildKit gRPC 连接断开（`error reading from server: EOF`），构建进程失去与构建器的通信而失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增了 scann 1.4.2 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套元数据文件。失败发生在 `dnf install` 步骤，当时正在下载软件仓库元数据（2.8 MB），尚未进入任何与 PR 代码逻辑相关的阶段。该步骤安装的包（`gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`）均为 openEuler 标准仓库包，Dockerfile 写法本身无误。

BuildKit 构建器的 `graceful_stop` 是 CI 基础设施层面的操作（节点回收、资源限制、维护窗口等），与代码提交无关。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是一个 CI 基础设施问题（BuildKit 构建器意外回收），应通过以下方式处理：
- 重新触发 CI 流水线（retry），确认构建器资源可用后再次执行
- 联系 CI 基础设施团队确认 `euler_builder` 节点的健康状态和回收策略

## 需要进一步确认的点
- 确认 `euler_builder_20260709_224657` 构建器被 `graceful_stop` 的原因（节点缩容、超时策略、手动终止等）
- 确认 CI 构建节点的资源限制是否存在不足导致构建器被回收（该 dnf 元数据下载速度仅 77 kB/s，可能因网络延迟导致构建耗时过长触发超时策略）
- 本次日志仅来自 x86-64 构建 job，若还有 aarch64 等并行架构 job 也处于失败状态，需获取其日志确认是否同为 infra 问题还是存在其他代码问题
