# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 异常终止
- 新模式症状关键词: graceful_stop, closing transport, error reading from server: EOF, no builder found

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`（`dnf install` 安装系统依赖阶段）
- 失败原因: BuildKit 构建容器 `euler_builder_20260709_224657` 在 `dnf install` 下载仓库元数据期间被优雅终止（`graceful_stop`），导致 RPC 传输关闭。构建器随后不再可用，构建无法继续。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了一个 Dockerfile（scann 1.4.2 在 openEuler 24.03-LTS-SP4 上的构建定义）及相关元数据文件。构建失败发生在 BuildKit 基础设施层面——构建器容器被意外终止，而非 Dockerfile 指令执行出错。第一步（拉取基础镜像）已成功完成，第二步（`dnf install` 安装系统包）刚开始下载元数据即被中断，属于 CI runner 侧的资源/环境问题。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 本次失败是 BuildKit 构建器容器的瞬时性基础设施故障（容器被优雅终止或资源回收），与 PR 代码完全无关。重新运行 CI job 极大概率可以成功通过。此类型的 `graceful_stop` / `closing transport` 错误通常是 CI 节点资源压力、调度策略或构建器生命周期管理异常导致的一次性问题。

## 需要进一步确认的点
- 构建节点 `ecs-build-docker-x86-hk` 在失败时段的资源使用状态（CPU/内存/磁盘），以排查是否因资源耗尽触发了 BuildKit 容器被清理
- CI 调度器是否对构建器容器有最大运行时间或资源限制，可能导致 `dnf install`（含网络下载）阶段的长时间等待触发回收

## 修复验证要求
无需代码修复。重新触发 CI 构建即可验证。
