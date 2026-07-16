# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器消失
- 新模式症状关键词: closing transport, graceful_stop, no builder found, euler_builder, goaway

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker BuildKit 构建器 `euler_builder_20260709_224657`（非代码层级）
- 失败原因: BuildKit 构建器在 Docker 镜像构建进行到第 2/4 步（`dnf install` 正在下载仓库元数据时）被主动优雅关闭（`graceful_stop`），随后构建器实例被移除，导致构建中断。该错误与 PR 代码变更完全无关，属于 CI 基础设施层面的构建器生命周期管理问题（可能由资源回收、超时或节点调度策略触发）。

### 与 PR 变更的关联
**无关。** PR 变更仅为新增 scann 1.4.2 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件（README.md、image-info.yml、meta.yml），属于标准的新平台支持流程。Dockerfile 语法正确，构建步骤合理。失败发生在 BuildKit 基础设施层面（构建器在 `dnf install` 下载元数据期间被回收），任何 Dockerfile 在此环境下均可能触发同类失败。

## 修复方向

### 方向 1（置信度: 高）
**无需修复代码。** 该失败为 CI 基础设施问题（BuildKit 构建器被提前回收），建议重新触发 CI 运行（retry）。如果在多次重试后仍反复出现同一错误，需要排查 CI 节点的 BuildKit 构建器资源配额、超时配置或节点健康状态。

## 需要进一步确认的点
- CI runner 节点 `ecs-build-docker-x86-hk` 上的 BuildKit builder 实例是否有资源限制或超时自动回收策略。
- 该构建器 `euler_builder_20260709_224657` 的 `graceful_stop` 是由外部调度系统触发还是 BuildKit 自身内部机制触发。
- 同类 PR 在同一时间段内是否有类似的基础设施故障模式（可用于判断是否为 CI 集群级别的间歇性问题）。
