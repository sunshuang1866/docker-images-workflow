# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 异常退出
- 新模式症状关键词: graceful_stop, rpc error: code = Unavailable, closing transport, no builder found

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Dockerfile 第 2/4 层 — `dnf install` 元数据下载阶段
- 失败原因: BuildKit builder 守护进程（`euler_builder_20260709_224657`）在构建过程中被异常关闭（`graceful_stop`），导致 DOCKER_BUILDKIT 客户端连接中断、builder 实例消失，构建被强制终止。

## 与 PR 变更的关联

**与 PR 变更无关。** PR 新增了一个完全标准的 Dockerfile，仅包含基础的 `dnf install` 构建依赖 + 编译安装 Python 3.9 + `pip install scann`，与同仓库现有其他 SP 版本的 Dockerfile 结构一致。构建尚未执行到 PR 特有逻辑——失败发生在最基础的 `dnf install` 步骤（拉取 OS 仓库元数据阶段），当时构建速度极慢（77 kB/s）且 BuildKit 服务端主动发送了 `graceful_stop` 信号后关闭，属于 CI 基础设施层面的异常。

## 修复方向

### 方向 1（置信度: 高）
**无需修复代码**。此为 CI 基础设施故障（BuildKit builder 被异常关闭），Code Fixer 无需处理任何文件。建议触发重新构建验证——基础设施恢复后，该 PR 的 Dockerfile 预期可正常通过构建。

## 需要进一步确认的点
- BuildKit builder 节点被 `graceful_stop` 的具体原因（资源不足被调度器驱逐、节点维护、超时等），需由 CI 基础设施运维排查。
- `dnf install` 阶段 77 kB/s 的低速是否触发了某种超时保护机制，可确认 CI runner 的出网带宽状况。
