# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 构建器异常终止
- 新模式症状关键词: gracefull_stop, error reading from server: EOF, no builder found, docker-container driver

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker BuildKit builder `euler_builder_20260709_224657`（容器内构建层 `#7 [2/4] RUN dnf install ...`，即 Dockerfile 中第一个 `dnf install` 步骤的 metadata 下载阶段）
- 失败原因: BuildKit 构建器 daemon 在 Docker 镜像构建过程中被优雅关闭（`graceful_stop`），导致与 builder 的 gRPC 连接中断（`error reading from server: EOF`）。此后 builder 实例被移除，CI 尝试继续访问时报 `no builder found`。该错误与 Dockerfile 内命令的执行逻辑无关，属于 CI 基础设施层面的构建器生命周期管理问题。

值得注意的是，dnf 在下载 OS 仓库元数据时网速仅约 77 kB/s（下载 2.8 MB 耗时 37+ 秒），网络延迟可能延长了构建耗时，使得构建更容易撞上 builder 实例的回收窗口。

### 与 PR 变更的关联
与 PR 变更无直接关联。PR 仅新增了一个标准的 Dockerfile（从 openEuler 24.03-LTS-SP4 基础镜像构建 scann，通过 pip 安装），该 Dockerfile 的 `dnf install` 步骤尚未完成 metadata 下载阶段，没有任何包安装错误或命令执行失败。构建器终止发生在基础设施层，与代码无关。

## 修复方向

### 方向 1（置信度: 中）
**触发 CI 重试/重新运行。** BuildKit builder 的 `graceful_stop` 是典型的 CI 基础设施瞬态故障（节点回收、资源清理等），通常重试即可恢复。另外 dnf metadata 下载速度仅 77 kB/s 可能是瞬态网络波动，重试时网络状况可能改善。

### 方向 2（置信度: 低）
如果重试持续失败且每次均在 dnf metadata 下载阶段出现类似超时/连接中断，需考虑：
- 检查 CI 构建节点的网络到 openEuler 24.03-LTS-SP4 DNF 仓库的连通性是否有问题
- 在 Dockerfile 中添加 dnf 重试逻辑（如 `dnf install --setopt=retries=5 ...`）

## 需要进一步确认的点
- BuildKit builder 被回收的具体原因（是 Jenkins 节点回收策略、资源限制、还是 builder 自身超时）。当前日志中仅有 `graceful_stop` 信息，缺乏 builder 的生命周期管理日志。
- 若重试后仍失败，需要获取 BuildKit daemon 自身的日志（非容器构建日志），以确认 builder 终止的真实触发条件。
- Dockerfile 中安装的 `zlib-devel`、`bzip2-devel` 等包在 openEuler 24.03-LTS-SP4 中是否存在且命名正确，本次构建未到达包解析阶段，无法验证。
