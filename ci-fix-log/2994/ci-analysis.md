# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 失联
- 新模式症状关键词: failed to receive status, no builder found, graceful_stop, closing transport, EOF, buildx_buildkit

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建的 `[2/4] RUN dnf install` 步骤（Dockerfile 行 `RUN dnf install -y ...`）
- 失败原因: Docker BuildKit builder 实例 `euler_builder_20260709_224657` 在执行 `dnf install` 过程中被意外终止（`graceful_stop`），导致 API 连接断开（EOF），构建进程无法继续。此为非代码层面的 CI 基础设施问题。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 新增的 Dockerfile 内容（安装编译工具链 → 编译 Python 3.9.19 → pip 安装 scann）逻辑正确，参考了同类镜像（scann 1.4.2 on 24.03-lts-sp3）的构建方式。构建在早期 `dnf install` 阶段因 BuildKit builder 容器异常终止而失败，并非 Dockerfile 指令错误导致。

## 修复方向

### 方向 1（置信度: 中）
重新触发 CI 构建。Builder 实例被 `graceful_stop` 终止通常由 CI 基础设施侧的资源回收、节点调度异常或 builder 空闲超时引起，重试大概率可恢复。若重试后仍失败，需检查 CI runner 节点的 BuildKit daemon 运行状态和资源配额。

## 需要进一步确认的点
- BuildKit builder `euler_builder_20260709_224657` 被终止的具体原因：查看 CI runner（`ecs-build-docker-x86-hk`）节点的系统日志，确认是否为 OOM Killer、磁盘满、或 Docker daemon 重启导致。
- 该 runner 节点上同时运行的其他构建任务是否存在资源争抢。
- 若重试多次均在同一位置（`dnf install`）失败，需排查该 `dnf` 仓库源在该节点的网络可达性和稳定性。
