# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器意外终止
- 新模式症状关键词: failed to receive status, closing transport, graceful_stop, no builder found, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在 `dnf install` 下载 OS 包阶段被优雅终止（`graceful_stop`），导致构建 gRPC 连接断开，后续步骤无法执行。日志显示构建仅进行了约 38 秒，`dnf` 正在以 77 kB/s 的低速下载元数据（已下载 2.8 MB）。Builder 发送了 `NO_ERROR` 的 GOAWAY 帧后关闭连接，排除代码错误导致的崩溃。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 失败发生在 `dnf install` 阶段，尚未执行到任何与 scann 或 Python 编译相关的步骤。PR 新增的 Dockerfile 安装依赖列表正确（`gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`），`pip install scann` 命令格式无误。该失败为 CI 基础设施层面的 BuildKit builder 异常终止，属于偶发性基础设施故障。

## 修复方向

### 方向 1（置信度: 高）
重新触发 CI 运行。此失败是 BuildKit daemon 在构建中途被意外终止所致，与代码无关，预计重试即可通过。常见触发方式：在 PR 评论中发送 `/retest` 或在 CI 平台手动重新运行失败的 job。

## 需要进一步确认的点
- 如果重新触发后仍反复出现同类错误，需排查 CI runner 节点上 BuildKit 服务的稳定性，检查是否存在 OOMKill、磁盘满或 daemon 自动重启等问题。
- 日志中 `dnf` 下载速度仅 77 kB/s，远低于正常水平。若重试后仍因相同步骤失败（如超时），需检查 runner 节点的网络状况或考虑为 `dnf` 配置更稳定的镜像源。
