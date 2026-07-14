# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器断连
- 新模式症状关键词: failed to receive status, rpc error, closing transport, graceful_stop, no builder found, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker BuildKit 构建器 `euler_builder_20260709_224657`（step `#7 [2/4]`，`dnf install` 执行期间）
- 失败原因: Docker BuildKit 临时构建器在构建进行中被外部信号终止（`graceful_stop`），客户端与构建器之间的 gRPC 连接断开，导致无法接收构建状态。构建器实例被移除后，后续重连尝试报 `no builder found`。构建在 step 2/4（`dnf install` 下载 OS 仓库元数据阶段，耗时 38.59 秒，速率 77 kB/s）时中断。

### 与 PR 变更的关联
**无关。** 该 PR 仅新增了 4 个文件（Dockerfile、README.md、image-info.yml、meta.yml），Dockerfile 内容为标准构建流程（安装系统依赖 → 编译 Python → pip 安装 scann）。构建在 `dnf install` 阶段因 BuildKit 基础设施故障中断，未抵达任何与 Dockerfile 内容相关的执行点。该失败属于 CI 基础设施问题，与 PR 代码变更无因果关系。

## 修复方向

### 方向 1（置信度: 中）
**触发 CI 重试。** 这是一个典型的 BuildKit 临时构建器被提前回收/超时终止的 infra 问题。`graceful_stop` 表明构建器收到了外部关闭信号（可能来自 CI 编排层的超时控制或节点资源回收）。由于错误发生在 dnf 元数据下载阶段（网络速率仅 77 kB/s），也可能是仓库镜像网络波动导致下载过慢，触发了构建器空闲超时。建议直接重跑 CI job。

### 方向 2（置信度: 低）
若重试后持续失败，检查 CI runner 节点的 Docker BuildKit 服务健康状态、节点磁盘空间及网络连通性。构建器 `euler_builder_20260709_224657` 名称中的时间戳（20260709）暗示可能是按日期创建的临时构建器池，若该批次构建器已过期回收，可能需要更新 CI 编排脚本中的构建器引用逻辑。

## 需要进一步确认的点
- 该次 CI 运行的 BuildKit 构建器是在 x86-64 还是 aarch64 runner 上创建（日志显示 runner 为 `ecs-build-docker-x86-hk`）
- 构建器 `euler_builder_20260709_224657` 是否因 CI job 级别的超时（如 10 分钟的构建超时）被强制终止
- dnf 元数据下载速率异常低（77 kB/s），需确认是否是该时间段的网络拥塞问题
- 该失败是否为孤立事件还是同一时间段多个 job 均受影响（检查同类仓库同时段 CI 结果）
