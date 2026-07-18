# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit builder 意外终止
- 新模式症状关键词: failed to receive status, rpc error, closing transport, graceful_stop, no builder found

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`（`dnf install` 下载元数据阶段），耗时约 38 秒处
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在构建过程中被意外停止（debug data 显示 `graceful_stop`），导致 gRPC 连接被关闭，构建中断。随后 builder 实例已不可用（`no builder found`）。

### 与 PR 变更的关联
与 PR 变更**无关**。本次 PR 仅新增了 scann 1.4.2 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），这些纯文本/配置变更不会导致 BuildKit builder 实例崩溃或连接中断。错误发生在 Docker 构建的第一条 `RUN` 指令执行期间（`dnf install`），且 builder 的 `graceful_stop` 表明是 CI 基础设施侧主动（或非预期）终止了 builder，属于环境/资源层面的偶发性故障。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码**。这是一个 CI 基础设施层面（BuildKit builder 实例意外终止）的偶发性故障，与 Dockerfile 内容或元数据变更无关。建议直接触发 CI 重试（re-run failed job），通常重新构建即可通过。

## 需要进一步确认的点
- BuildKit builder `euler_builder_20260709_224657` 为何被 `graceful_stop`：可能是 CI runner 节点资源不足（内存/磁盘）、构建超时策略触发、或运维操作导致 builder 被回收。建议检查对应时间段的 runner 节点日志和资源使用情况。
- 若重试后仍然在相同步骤失败（`dnf install` 阶段），则需排查 openEuler 24.03-lts-sp4 基础镜像的仓库元数据是否有网络或镜像站问题。
