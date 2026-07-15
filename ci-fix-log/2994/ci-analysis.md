# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit builder 被终止
- 新模式症状关键词: graceful_stop, closing transport, connection error: EOF, no builder found

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建阶段，步骤 `#7 [2/4] RUN dnf install ...`（Dockerfile 第 7 行附近，`dnf install` 命令执行期间）
- 失败原因: Docker BuildKit builder (`euler_builder_20260709_224657`) 在 `dnf install` 下载仓库元数据过程中被外部信号优雅终止（`graceful_stop`），导致 gRPC 连接断开、传输关闭。builder 被清除后，后续操作无法找到该 builder 实例。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了一个标准的 Dockerfile（安装 gcc 工具链 → 安装 Python 3.9 → pip 安装 scann）和相关元数据文件。构建失败发生在基础设施层面——Docker BuildKit builder 进程在运行时被外部终止，PR 代码本身不存在语法或逻辑错误。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建即可。** 这是 CI 基础设施的偶发性故障，常见原因包括：
- CI runner 节点资源不足（内存 / 磁盘）导致 buildkit 容器被 OOM Killer 终止
- Jenkins job 超时阈值触发，外部终止了 builder 子进程
- 网络波动导致 gRPC keepalive 超时，buildkit 主动发起 graceful_stop

Code Fixer 无需修改任何代码。建议直接 `/retest` 或在 Jenkins 上重新触发该 job。

## 需要进一步确认的点
- 检查 Jenkins 构建节点 `ecs-build-docker-x86-hk` 在对应时间段的资源使用情况（内存、磁盘、CPU），确认是否为 OOM 或磁盘满导致的 builder 终止。
- 检查该 job 的超时配置，确认 `dnf install` 步骤是否因下载 OpenELA 仓库元数据慢而触发了超时。
- 查看同一时间段其他 PR 的构建情况，判断是否为该 runner 节点的系统性问题而非本次独占。
