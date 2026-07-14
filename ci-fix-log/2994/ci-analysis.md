# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit 构建器被终止
- 新模式症状关键词: graceful_stop, goaway, no builder found, rpc error, closing transport, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 [2/4]（`dnf install` 下载仓库元数据阶段）
- 失败原因: BuildKit 构建器 `euler_builder_20260709_224657` 在构建过程中被 CI 基础设施主动终止（goaway 帧携带 `graceful_stop` 标志），导致正在执行的 `dnf install` 步骤因 gRPC 连接断开而失败，随后构建器被清理（`no builder found`）。

### 与 PR 变更的关联
**与 PR 无关**。PR 新增的 Dockerfile 内容为标准操作（`dnf install` 系统包 → 编译安装 Python 3.9.19 → `pip install scann`），步骤 [2/4] 的 `dnf install` 命令语法正确，所安装的包名（`gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`）均为 openEuler 仓库的标准包。失败发生在 dnf 下载元数据过程中构建器被基础设施终止，与 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。该失败为基础设施层面的瞬时故障（BuildKit builder 被主动终止），Dockerfile 代码本身无需修改。操作：在 PR 页面使用 `/retest` 或类似的 CI 重试命令重新触发构建流水线。如果多次重试均在同一位置失败，则可能需要排查 CI runner 节点的资源或网络问题。

## 需要进一步确认的点
- 若重试后仍失败，需确认该 CI runner（`ecs-build-docker-x86-hk`）是否存在资源不足（磁盘/内存）或网络带宽瓶颈（日志中 dnf 下载速度仅 77 kB/s，2.8 MB 元数据预计需约 37 秒，可能触发某种隐形超时）。
- 日志中仅包含 x86-64 架构的构建记录，需确认 aarch64 架构的构建是否也失败及具体原因。
- 确认 `euler_builder` builder 实例的生命周期管理策略，是否存在单次构建的时间上限。
