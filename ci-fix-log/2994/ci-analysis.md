# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: 构建器会话丢失
- 新模式症状关键词: graceful_stop, no builder found, closing transport, EOF, buildx, buildkit

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Dockerfile 第 8 行 `RUN dnf install ...` 步骤（Docker build 阶段 2/4）
- 失败原因: Docker buildx 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 过程中被主动关闭（`graceful_stop`），导致与构建器的 gRPC 连接断开（`closing transport`）。构建进行了约 39 秒后，构建器实例已不存在（`no builder found`），Docker build 彻底失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了一个标准的 Dockerfile（安装系统依赖 → 编译 Python 3.9.19 → pip 安装 scann），以及配套的 README、image-info.yml、meta.yml 元数据更新。构建在第一个 `dnf install` 步骤进行到约 39 秒时因 CI 基础设施层面的构建器会话丢失而中断，远未到达可能由代码错误导致的失败阶段。`dnf install` 的依赖包列表（gcc、gcc-c++、make、wget、openssl-devel、bzip2-devel、zlib-devel）均为 openEuler 仓库中的标准包，无异常。

## 修复方向

### 方向 1（置信度: 低）
**重试 CI 构建。** 该失败属于 CI 基础设施层面的偶发性问题（buildx builder 实例被提前回收），重新触发 CI 构建大概率可以通过。`graceful_stop` 表明构建器是正常关闭而非异常崩溃，可能由以下原因之一引起：
- CI runner 的构建器会话 TTL 到期
- 构建节点资源回收调度
- 构建器守护进程重启

无需对 Dockerfile 或任何 PR 文件做代码层面的修改。

## 需要进一步确认的点
- **构建器回收原因**: 需要从 CI 平台运维侧确认 `euler_builder_20260709_224657` 被 `graceful_stop` 的具体原因（是否触发了超时策略、内存/磁盘限制，或是节点维护计划）。
- **构建实际耗时**: 日志中 `dnf install` 仅运行了约 39 秒即被中断，若 CI 平台有构建步骤的最长执行时间限制，需要确认该限制值是否过短。
- **重试结果**: 建议重新触发 CI 构建至少 2 次，观察是否稳定复现。若能稳定复现，则根因可能不是 infra-error，需要进一步获取失败时的完整日志。
- **网络状况**: 日志显示 `dnf` 元数据下载速度为 `77 kB/s`（偏低），若 CI 构建环境存在网络波动，可能放大了构建时间，间接导致触发构建器回收策略。
