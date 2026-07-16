# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit 构建器连接中断
- 新模式症状关键词: rpc error, Unavailable, closing transport, grace_stop, no builder found, BuildKit

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4] RUN dnf install ...`，Dockerfile 路径 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`
- 失败原因: CI 使用的 BuildKit builder 实例 `euler_builder_20260709_224657` 在执行 `dnf install` 期间被发起 `graceful_stop`（优雅关闭），导致 gRPC 传输层连接断开，客户端无法接收构建状态，随后 builder 实例被销毁（`no builder ... found`），构建中断失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了一个 Dockerfile、更新了 README.md、image-info.yml 和 meta.yml，Dockerfile 内容为标准软件安装流程（安装系统依赖 → 编译 Python 3.9.19 → pip 安装 scann），无代码错误或配置问题。构建在执行 `dnf install` 的第一阶段就因 builder 连接中断而失败，属于 CI 基础设施层面的瞬态故障。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重试 CI 即可。** 该失败是 BuildKit builder 实例在执行构建过程中被意外终止导致的连接中断，属于 CI 基础设施瞬态故障。建议在 Jenkins 中手动重新触发该 job 或 push 一个空 commit 触发重试。若重试后仍然失败，需排查 CI builder 节点的资源（内存/磁盘）或调度策略是否存在问题。

## 需要进一步确认的点
- 若重试后问题依然出现，需确认该 BuildKit builder 节点（`ecs-build-docker-x86-hk`）的资源是否充足（内存、磁盘空间），是否存在 OOM 或磁盘满导致 builder 进程被终止的情况。
- 确认 CI 调度层是否对构建任务有超时或资源配额限制，导致 builder 在 dnf 元数据下载阶段被强制关闭。
