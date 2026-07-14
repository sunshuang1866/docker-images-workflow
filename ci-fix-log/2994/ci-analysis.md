# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit builder 被终止
- 新模式症状关键词: graceful_stop, no builder found, error reading from server: EOF, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建层 `[2/4] RUN dnf install ...`（Dockerfile 第 7 行 `dnf install` 步骤）
- 失败原因: Docker BuildKit 构建器实例 `euler_builder_20260709_224657` 在构建过程中被优雅关闭（`graceful_stop`），导致与 builder 的 gRPC 连接中断（`closing transport`），构建任务无法继续。构建正处在拉取 openEuler OS 软件包元数据阶段，距离开始约 38 秒，尚未进入任何编译或安装逻辑。

### 与 PR 变更的关联
**无关。** PR #2994 的新增 Dockerfile 是一个全新的文件，语法正确，所安装的依赖包（`gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`）均为 openEuler 标准仓库包名。构建失败发生在 `dnf install` 下载元数据的过程中——此时连第一个包都还没开始安装，无法判定 PR 代码本身有任何问题。失败根因是 CI 基础设施层 BuildKit builder 实例异常终止。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 这是一次性的 BuildKit 基础设施故障（builder 实例被优雅关闭，原因可能是 CI 节点资源耗尽、builder 超时或节点维护）。Code Fixer 无需修改任何代码。重跑 CI job 大概率可通过。

### 方向 2（置信度: 低）
如果重试后仍反复出现同样的 `graceful_stop` 错误，需由 CI 运维团队排查构建节点的 Docker BuildKit（buildx）配置，检查 builder 实例的生命周期管理策略（如空闲超时、并发限制、资源配额等）。

## 需要进一步确认的点
1. 相同 PR 是否在其他架构（aarch64）runner 上也有构建任务，且是否也出现同类错误？
2. CI 节点 `ecs-build-docker-x86-hk` 上的 buildx builder 是否有已知的稳定性问题或不合理的超时配置？
3. 如果重试后失败模式变化（如出现 `dnf` 包名不存在等错误），则需重新分析。
