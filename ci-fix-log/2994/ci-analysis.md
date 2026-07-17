# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器优雅关闭
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
- 失败位置: `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile:7`（`dnf install` 步骤）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 下载仓库元数据时被优雅关闭（`graceful_stop`），导致 gRPC 连接中断，后续尝试查找该 builder 时报 `no builder found`。

### 与 PR 变更的关联
**无关。** PR 新增的 Dockerfile 语法正确，`dnf install` 列出的包名（`gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`）均为 openEuler 24.03-LTS-SP4 仓库的标准可用包。构建失败发生在 dnf 下载元数据阶段，BuildKit builder 被外部原因终止，与 PR 代码变更无因果关系。

## 修复方向

### 方向 1（置信度: 高）
**无需修复。** 此为 CI 基础设施临时故障（BuildKit builder 被 GracefulStop 终止），不是代码问题。重新触发 CI 流水线即可。若该问题反复出现，应由 CI 运维团队排查 builder 节点的资源/超时/稳定性配置。

## 需要进一步确认的点
- CI 构建节点 `ecs-build-docker-x86-hk` 上的 builder `euler_builder_20260709_224657` 是否因资源耗尽（内存/磁盘）被 OOM killer 或调度器回收。
- builder 的 idle timeout / max lifetime 配置是否会导致长时间运行的 `dnf install`（下载大体积元数据时）触发自动回收。
- 确认 `graceful_stop` 是来自 BuildKit daemon 的主动终止（如运维操作）还是资源限制触发的被动回收。
