# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit builder 失联
- 新模式症状关键词: `failed to receive status`, `rpc error`, `closing transport`, `builder.*not found`, `graceful_stop`

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker build 阶段 `#7 [2/4]`（`dnf install` 正在下载 metadata 时）
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在 Docker 构建过程中被优雅终止（`graceful_stop`），导致客户端与 builder 的连接断开（`error reading from server: EOF`），后续操作无法找到该 builder（`no builder found`）。这是 CI 基础设施层面的问题，与 PR 代码变更无关。

### 与 PR 变更的关联
**与 PR 无关。** PR 新增的 Dockerfile 语法正确、依赖声明完整，构建过程仅执行到第 2 步（共 4 步）的 `dnf install` 阶段就被基础设施中断。该 Dockerfile 镜像在 x86-64 架构上也存在同名 sp3 版本（`Others/scann/1.4.2/24.03-lts-sp3/Dockerfile`，同样使用 openEuler 24.03 系列基础镜像），CI 历史上未报告过该路径下的 `dnf` 元数据下载或包安装问题。

## 修复方向

### 方向 1（置信度: 高）
无需修改 PR 代码。这是 CI 基础设施中 BuildKit builder 的偶发性失联问题（可能由节点资源回收、网络抖动或 builder 超时自动清理触发）。重新触发 CI 流水线即可。

### 方向 2（置信度: 低）
如果重试后仍然失败，可能需要检查 CI 的 builder 超时配置或节点资源水位，但这属于运维层面，非 Code Fixer 职责范围。

## 需要进一步确认的点
- 确认该 CI 节点（`ecs-build-docker-x86-hk`）在失败时段的资源状态和 builder 超时策略。
- 确认重试后是否通过（该错误模式通常为重试后可恢复的偶发故障）。
