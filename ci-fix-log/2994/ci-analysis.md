# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit 构造器崩溃
- 新模式症状关键词: failed to receive status, closing transport, error reading from server: EOF, graceful_stop, no builder found, rpc error

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker BuildKit 构建阶段 `[2/4]`（`dnf install` 步骤）
- 失败原因: Docker BuildKit 构造器 `euler_builder_20260709_224657` 在 `dnf install` 下载系统包过程中被终止（`graceful_stop`），导致客户端断开连接（`error reading from server: EOF`），后续无法找到该 builder。`dnf` 下载元数据耗时 38.59 秒，速率仅 77 kB/s，表明该 CI runner 网络状况极差，可能因此触发 CI 基础设施的超时/资源回收机制，杀死了 BuildKit 守护进程。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 仅新增了一个标准的 scann Dockerfile（安装 gcc/make/openssl-devel/bzip2-devel/zlib-devel、编译 Python 3.9、pip install scann），以及更新了 README.md、image-info.yml 和 meta.yml。失败发生在最基础的 `dnf install` 步骤（第 2 个构建步骤），该命令在所有 openEuler Dockerfile 中普遍存在，并非本次 PR 引入的特殊逻辑。构建本身尚未到达任何与 scann 或 Python 有关的步骤。

## 修复方向

### 方向 1（置信度: 中）
**重新触发 CI 构建**。该失败为 CI 基础设施问题（BuildKit 构造器被异常终止），与代码变更无关。最可能的原因为 CI runner 网络波动（dnf 下载速率仅 77 kB/s）导致构建超时，runner 上的 BuildKit 实例被清理。如果多次重试后仍反复出现同样问题，则需要排查该 runner 节点（`ecs-build-docker-x86-hk`）的网络状况或 BuildKit 守护进程配置。

### 方向 2（可选）
如果重试后依然在 `dnf install` 阶段超时，可在 Dockerfile 中为 dnf 配置更近的镜像源或添加 `--setopt=timeout=300` 提高 dnf 内部超时阈值，但这不是根本解决方案——根本问题在于 CI runner 的网络质量。

## 需要进一步确认的点
- CI runner `ecs-build-docker-x86-hk` 在事发时段的网络连通性和带宽状况
- BuildKit 构造器 `euler_builder_20260709_224657` 是否被 CI 平台的任务超时策略（如 60 秒无输出则 kill）所终止
- 同一时段其他 PR 是否也在该 runner 上出现同类 BuildKit 连接断开问题
