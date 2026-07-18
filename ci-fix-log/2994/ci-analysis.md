# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 崩溃
- 新模式症状关键词: closing transport, error reading from server: EOF, goaway, graceful_stop, no builder found, docker-container driver

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
- 失败原因: BuildKit 构建实例 `euler_builder_20260709_224657` 在 DNF 安装依赖包过程中异常终止（`graceful_stop`），导致客户端 gRPC 连接断开（`error reading from server: EOF`），构建中断。

### 与 PR 变更的关联
**与 PR 变更无关**。该 PR 仅新增了 openEuler 24.03-lts-sp4 版本的 Dockerfile（内容与已有的 24.03-lts-sp3 版本结构一致，仅基础镜像标签从 `24.03-lts-sp3` 变更为 `24.03-lts-sp4`）、meta.yml 条目、README.md 引用和 image-info.yml 条目。Dockerfile 语法正确，`dnf install` 命令包名均为 openEuler 24.03 仓库中存在的标准开发工具包。失败发生在 CI 的 BuildKit 基础设施层（builder 崩溃），属于典型的 infra-error。

## 修复方向

### 方向 1（置信度: 高）
重新触发 CI 运行。BuildKit builder 实例 `graceful_stop` 通常由 CI 节点的资源压力、Docker BuildKit 守护进程重启、或临时的节点网络抖动引起，属于临时性基础设施故障。PR 代码无需任何修改，重试 CI 大概率可通过。

## 需要进一步确认的点
- 如果多次重试后仍在同一位置失败，需检查 CI Runner 节点 `ecs-build-docker-x86-hk` 上 BuildKit 守护进程的健康状态及资源配额（内存/磁盘）。
- 确认 `euler_builder_*` 命名风格的 builder 实例是否存在自动回收策略，该回收策略是否与镜像构建时间冲突（DNF 下载较慢时可能超过 builder 租约时间）。

## 修复验证要求
无需验证。本失败为 infra-error，与代码变更无关。
