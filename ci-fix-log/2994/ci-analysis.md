# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器断开
- 新模式症状关键词: failed to receive status, closing transport, graceful_stop, no builder found, euler_builder

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: 构建阶段 Step #7（`RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`），由 BuildKit 守护进程 `euler_builder_20260709_224657` 执行
- 失败原因: BuildKit 构建器 `euler_builder_20260709_224657` 被外部终止（`graceful_stop`），导致正在执行的 dnf install 指令连接断开，属于 CI 基础设施级别的异常

### 与 PR 变更的关联
与 PR 变更**无关**。本次 PR 仅新增了一个标准结构的 Dockerfile（安装系统包 → 编译 Python → pip 安装 scann），未引入任何可能导致构建器崩溃或异常退出的代码。dns install 指令本身是正确且常规的操作。失败发生在 Jenkins 构建节点（`ecs-build-docker-x86-hk`）上 BuildKit 守护进程被外部因素终止，属于基础设施故障。

## 修复方向

### 方向 1（置信度: 高）
直接重试构建。BuildKit 构建器被 `graceful_stop` 终止是瞬态基础设施问题（可能由节点资源压力、网络抖动超时或宿主机运维操作触发），与本次 PR 的 Dockerfile 内容无关。对该 PR 重新触发 CI 即可，无需修改任何代码。

### 方向 2（置信度: 低）
如果重试后仍反复出现相同错误，则需检查 Jenkins 构建节点 `ecs-build-docker-x86-hk` 的资源状态（内存、磁盘）以及 BuildKit 配置（`--oci-worker-gc`、`--keep` 等参数），排查是否存在因 `dnf` 下载速度过慢（本次日志为 77 kB/s）触发 BuildKit inactivity 超时的可能。

## 需要进一步确认的点
- 日志中 `euler_builder_20260709_224657` 被 `graceful_stop` 的具体原因未在提供的日志中记录——需要查看 BuildKit 守护进程自身的日志（journalctl 或容器日志）来确认终止的直接触发条件
- 若重试后仍失败，需确认构建节点的网络状况（dnf 元数据下载仅 77 kB/s 是否属于节点常态）、内存配额以及同节点上其他构建任务是否存在资源竞争
