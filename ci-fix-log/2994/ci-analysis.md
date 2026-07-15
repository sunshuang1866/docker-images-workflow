# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 构建守护进程连接丢失
- 新模式症状关键词: rpc error, closing transport, connection error, graceful_stop, no builder found, buildkit

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 #7（`dnf install` 软件包阶段），构建进程运行约 38.59 秒时
- 失败原因: BuildKit 构建守护进程（`euler_builder_20260709_224657`）被 CI 平台主动触发 `graceful_stop`，导致正在执行 `dnf install` 的 Docker 构建连接中断。`graceful_stop` 是 BuildKit 收到 SIGTERM 后的正常关闭流程，说明 CI 平台因超时或资源回收主动终止了该 builder 实例。第二条错误 `no builder found` 是 builder 已销毁后的连带后果。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 仅新增了一个标准 Dockerfile（安装编译依赖 + 编译 Python 3.9 + pip 安装 scann），以及 README/meta.yml/image-info.yml 等元数据文件更新。没有任何代码改动能够触发 BuildKit builder 被 CI 平台终止。`dnf install` 正在正常下载仓库元数据时（OS 仓库 2.8 MB，下载中），builder 被外部终止，属于纯粹的 CI 基础设施事件。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复，需要重新触发 CI 构建。** 此失败为 CI 基础设施层面的 buildkit builder 连接中断（`graceful_stop`），与 PR 代码变更无关。建议在 CI 平台重新触发该 Job，若再次同样失败，需排查 CI runner 节点的资源状况（内存不足 OOM、磁盘空间不足、或构建超时被平台 kill）。

## 需要进一步确认的点
- CI runner 节点（`ecs-build-docker-x86-hk`）在构建期间的资源使用情况（内存、磁盘是否耗尽导致 builder 被 kill）
- 构建是否有硬性超时限制，本次 `dnf install` 下载阶段耗时约 38.59 秒是否触发了某个中间层超时阈值
- `graceful_stop` 的触发来源：是 CI 平台的作业超时机制还是 kubernetes pod 驱逐/资源回收
