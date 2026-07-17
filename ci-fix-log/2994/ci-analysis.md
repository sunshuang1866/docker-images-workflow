# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器被终止
- 新模式症状关键词: graceful_stop, no builder found, rpc error: code = Unavailable, closing transport, error reading from server: EOF, buildx

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker build 步骤 #7（`dnf install` 阶段），Dockerfile `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 第 9 行
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 下载软件包过程中被 CI 系统以 `graceful_stop` 方式终止，导致与构建器的 RPC 连接断开（`closing transport`），此后构建器已不可用（`no builder found`），整个 Docker 构建失败。

### 与 PR 变更的关联
PR 变更与失败**无直接关联**。PR 仅新增了 4 个文件：一个标准的 Dockerfile、README 条目、image-info.yml 条目和 meta.yml 条目。失败发生在 Docker 构建的 `dnf install` 基础系统包安装阶段——该阶段尚未接触到 PR 引入的任何业务逻辑代码。`dnf install` 命令本身是 openEuler 环境下的标准包管理操作，不存在语法或逻辑错误。`graceful_stop` 信号来自 CI 编排层，属于基础设施层面的事件。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施问题——BuildKit 构建器被平台提前回收。

`graceful_stop` 带有 `NO_ERROR` 标记，说明构建器本身运行正常，是被 CI 编排系统主动终止的。可能原因包括：
- Jenkins job 或 buildx builder 达到超时上限（`dnf install` 已运行 38+ 秒且仍在下载元数据，Docker 构建整体耗时可能超过 CI 配置的 step 超时）
- CI runner（`ecs-build-docker-x86-hk`）资源紧张，builder 容器被调度系统驱逐
- 网络波动导致与 builder 的 gRPC 连接中断

**建议操作**: 重新触发 CI 运行（retry）。如果反复出现相同错误，联系 CI 基础设施团队检查 runner 上的 buildx builder 资源池状态和超时配置。此失败无需修改 PR 代码。

## 需要进一步确认的点
1. CI runner `ecs-build-docker-x86-hk` 上的 buildx builder 实例是否有存活时间（TTL）限制，是否会在构建耗时较长时自动回收
2. 本次构建的 `dnf install` 步骤是否有额外的下载耗时（如 mirrors 响应慢），导致总构建时间触发了某个超时阈值
3. 同时间段是否有其他构建共享同一 builder 实例，是否存在资源争抢
4. 重新触发 CI 后是否仍然复现——如果复现，需检查 `openeuler:24.03-lts-sp4` 基础镜像的 dnf repo 配置是否在 CI 网络环境中可达
