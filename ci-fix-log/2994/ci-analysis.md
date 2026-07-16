# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器意外终止
- 新模式症状关键词: failed to receive status, rpc error, closing transport, connection error, graceful_stop, no builder found

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4]` — `RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`
- 失败原因: BuildKit 构建器容器（`euler_builder_20260709_224657`）在 `dnf install` 下载软件包过程中被终止，gRPC 传输连接断开（`graceful_stop`）。dnf 下载速度极慢（仅 77 kB/s），可能因下载耗时过长触发 CI 超时或导致与构建器守护进程的连接超时，构建器被清理后构建中断。

### 与 PR 变更的关联
与 PR 变更**无直接关联**。PR 新增的 Dockerfile 语法正确，`dnf install` 安装的均为 openEuler 仓库标配开发工具包（gcc、openssl-devel、bzip2-devel、zlib-devel），不存在拼写错误或不存在的包名。构建在第 2 个 Docker 层（`dnf install`）因 BuildKit 基础设施故障中断，尚未进入后续的 Python 编译或 pip 安装阶段。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施问题，Code Fixer **无需处理**。这是 BuildKit 构建器在构建过程中被意外终止的 transient infra-error。建议在 CI 侧排查：
- 构建节点的网络状况（`dnf` 下载 `openEuler` 仓库元数据仅 77 kB/s 异常缓慢，可能是网络波动导致整体构建超时）
- 构建器容器的超时设置是否过短
- 构建节点资源（内存/磁盘）是否充足

### 方向 2（置信度: 低）
如果该问题持续复现，可能是 openEuler 24.03-LTS-SP4 基础镜像的默认 dnf 仓库镜像源在 CI 环境中网络不稳定。可考虑在 Dockerfile 中添加 `sed` 切换为更可靠的镜像源后再执行 `dnf install`，但当前证据不足以确认此为根因，不建议在首次失败时修改 Dockerfile。

## 需要进一步确认的点
1. 同一 PR 在重新触发 CI 后是否能通过（若重试成功，则确认为 transient infra-error）
2. CI 构建节点的出网带宽和 `repo.openeuler.org` 可达性
3. BuildKit `docker-container` driver 的超时配置（`--builder-timeout` 等参数）
4. 是否存在同批次其他 PR 也出现相同告警（若集中出现，说明 CI 基础设施整体不稳定）
