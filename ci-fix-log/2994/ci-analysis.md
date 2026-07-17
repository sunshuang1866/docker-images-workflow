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
- 失败位置: Docker 构建步骤 `[2/4]`，正在执行 `dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`（dnf 元数据下载阶段，已运行约 38.59 秒）
- 失败原因: CI 使用的 Docker BuildKit builder 实例 `euler_builder_20260709_224657` 在构建过程中被上层 CI 基础设施优雅终止（goaway frame 携带 `graceful_stop` 指令和 `NO_ERROR` 状态码），导致 gRPC 传输连接断开，Docker build 无法继续。这不是 PR 代码变更引起的构建逻辑错误，而是 CI 构建节点/调度器层面的基础设施问题。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 内容正确：`dnf install` 包的列表中均为 openEuler 24.03-LTS-SP4 标准仓库下的有效包名（gcc、gcc-c++、make、wget、openssl-devel、bzip2-devel、zlib-devel），Dockerfile 语法无错误。构建在 dnf 元数据下载阶段（尚未进入实际包安装）即因 builder 被外部终止而失败，属于 CI 基础设施异常。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题，无需修改 PR 代码。重新触发 CI 构建（re-run / re-trigger）即可。若反复出现同类问题，需排查 CI 调度器对 `euler_builder_*` 构建器的生命周期管理是否异常（如是否存在全局超时过早终止 builder 的情况）。

## 需要进一步确认的点
- 日志中 dnf 元数据下载速度为 77 kB/s（2.8 MB 元数据），速度偏慢，需确认 openEuler 24.03-lts-sp4 基础镜像内置的 dnf repo 源在 CI 构建节点的网络连通性是否正常。若反复因 dnf 下载超时触发 builder 终止，可能需要调整 dnf repo mirror 配置或延长 CI 步骤超时阈值。
- `euler_builder_20260709_224657` 被终止的具体原因（CI 编排层是否设定了构建步骤的最大执行时间，是否触发了节点抢占等）。此信息需要从 CI 编排层日志（trigger job 或 scheduler 日志）获取。
