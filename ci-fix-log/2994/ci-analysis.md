# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器被终止
- 新模式症状关键词: graceful_stop, no builder found, closing transport, rpc error, Unavailable

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 #7（`RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 下载系统包过程中被外部组件主动终止（`graceful_stop`），导致与构建器的 gRPC 连接断开，Docker 构建中断。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准的 openEuler 24.03-LTS-SP4 Dockerfile（21 行，包含 `dnf install` 构建依赖 + Python 3.9.19 编译安装 + pip 安装 scann）及相关元数据文件和 README 条目。日志显示 Docker 构建在正常执行 `dnf install` 阶段（下载系统软件包）时，BuildKit 构建器被外部原因终止。构建本身尚未到达任何与 PR 代码逻辑相关的阶段，Dockerfile 语法也无错误（`load build definition from Dockerfile` 成功）。根据构建日志显示，操作系统包下载进行到 38 秒时 BuildKit 节点被外部组件执行了优雅停机（graceful_stop），之后客户端无法再找到该构建器。此模式常见于 CI 基础设施资源回收、节点下线维护或构建时间超限被强制终止。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 这是一个 CI 基础设施问题，应由 CI 运维团队排查。可能的原因包括：
- 构建节点资源不足（内存/磁盘）导致 Docker BuildKit daemon OOM 被 kill
- 构建节点在构建过程中被调度系统回收或下线维护
- `docker-container` driver 的 BuildKit 实例超出了资源配额被清理

建议：重新触发 CI 构建（retry），观察是否复现。若反复在同一步骤失败，则需排查构建节点的资源配额。

## 需要进一步确认的点
- 构建节点 `ecs-build-docker-x86-hk` 的资源状态（内存、磁盘、CPU）在构建失败时刻是否正常
- BuildKit daemon 日志中 `graceful_stop` 的触发源头（是手动下线、自动弹性伸缩，还是资源限制触发）
- 该 PR 是否可以单独重试成功，以排除是一次性的基础设施波动
