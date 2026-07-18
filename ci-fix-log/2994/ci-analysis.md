# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 构建器连接中断
- 新模式症状关键词: graceful_stop, no builder found, connection error, rpc error Unavailable

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker buildx builder 实例 `euler_builder_20260709_224657`（基础设施层面，非代码层面）
- 失败原因: BuildKit builder 实例在 Docker 构建过程中被关闭（goaway reason: `graceful_stop`），导致客户端与 builder 之间的 gRPC 连接中断，处于步骤 `#7 [2/4] RUN dnf install ...` 的构建任务无法继续执行，报 transport 关闭错误后失败。builder 实例关闭后已不可用（"no builder found"）。

### 与 PR 变更的关联
**与 PR 无关。** PR 变更仅新增了一个标准 Dockerfile（scann 1.4.2 在 openEuler 24.03-lts-sp4 上的构建文件）及配套的 README.md、image-info.yml、meta.yml 元数据更新。构建在第一个 `RUN dnf install` 步骤（安装基础编译工具）中即中断，该步骤内容与相邻镜像（24.03-lts-sp3）完全一致，且 `dnf` 本身已成功启动并正在同步元数据（38.59 秒内下载了 2.8 MB），失败纯因 builder 实例被外部关闭。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 CI 基础设施故障——BuildKit builder 实例 `euler_builder_20260709_224657` 被调度系统或运维操作关闭（`graceful_stop`），导致正在进行中的 build 会话中断。应：
1. 触发该 PR 的 CI 重新构建（retry）。
2. 若多次重试仍出现同类问题，需由 CI 运维排查 builder 节点是否因资源回收、节点轮换等策略在构建过程中被提前终止。

## 需要进一步确认的点
- builder 实例 `euler_builder_20260709_224657` 被 `graceful_stop` 的原因（是否为 CI 平台侧的资源回收策略、节点下线或超时设置触发）。
- 该 PR 的同类镜像（如 scann 1.4.2 on openEuler 24.03-lts-sp3）在同时段是否也受 builder 关闭影响——可用来佐证是否为基础设施侧的系统性问题。

## 修复验证要求
无。此次失败为 infra-error，无需代码修改，在 CI 重新运行后观察是否通过即可。
