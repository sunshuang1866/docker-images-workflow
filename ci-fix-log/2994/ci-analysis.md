# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 掉线
- 新模式症状关键词: failed to receive status, rpc error, Unavailable, graceful_stop, no builder found

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建阶段 Step `#7 [2/4]`（`dnf install` 步骤执行期间）
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在构建中途被优雅关闭（`graceful_stop`），导致与 builder 之间的 gRPC 连接断开（`connection error: EOF`），处于运行中的 `dnf install` 步骤随之失败。该错误属于 CI 基础设施层面问题，与 PR 代码无关。

### 与 PR 变更的关联
PR 变更仅新增了 scann 1.4.2 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及相关元数据文件（README.md、image-info.yml、meta.yml），新增的 Dockerfile 语法正确、依赖声明完整。CI 构建在 `dnf install` 阶段因 BuildKit builder 进程退出而中断，**与 PR 代码变更无关**——这是一个 CI 基础设施瞬态故障，构建流程尚未到达软件安装/编译阶段。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题，**无需修改 PR 代码**。重新触发 CI 流水线即可。若频繁复现，需由 CI 运维排查 BuildKit builder 节点（`ecs-build-docker-x86-hk`）的资源或稳定性问题。

## 需要进一步确认的点
- 该 BuildKit builder 掉线是否在该 CI runner 上频繁发生（检查同一 runner 上其他近期构建的历史）
- runner 节点资源（内存/磁盘）是否充足，`graceful_stop` 是否由 OOM/磁盘满触发
