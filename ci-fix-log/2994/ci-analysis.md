# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit builder 意外终止
- 新模式症状关键词: failed to receive status, rpc error, Unavailable, closing transport, graceful_stop, no builder found, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`（`dnf install` 阶段，正在下载 openEuler 仓库元数据）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在 Docker 构建中途被优雅终止（`graceful_stop`），导致与 builder 的连接断开。日志显示 `dnf` 下载元数据速度极慢（77 kB/s），耗时超过 37 秒，可能触发了构建超时或 runner 资源清理。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 及相关元数据/文档文件。Docker 构建在执行第一个 `RUN dnf install` 步骤（安装基础编译依赖）时就因 BuildKit builder 崩溃而中断，尚未到达任何与 scann 软件本身相关的步骤。失败属于 CI 基础设施层面的问题。

## 修复方向

### 方向 1（置信度: 中）
**重试构建**。该失败为 BuildKit 基础设施瞬时故障（builder 被优雅终止），与 PR 代码无关。建议 CI 管理员检查 `ecs-build-docker-x86-hk` runner 节点的 BuildKit builder 配置（超时设置、资源限制），然后重新触发 CI 运行。大概率可成功通过。

### 方向 2（置信度: 低）
若重试仍失败，需排查 `dnf install` 阶段是否因网络问题（openEuler 仓库 `77 kB/s` 的极慢下载速度）导致构建超时。可在 CI 环境中验证 `repo.openeuler.org` 的可达性和带宽。

## 需要进一步确认的点
1. 确认 `ecs-build-docker-x86-hk` runner 节点上 BuildKit builder 的存活时间（TTL）配置，是否因 `dnf` 下载过慢导致 builder 超时自动回收。
2. 确认 runner 节点在执行构建期间的资源状态（内存、磁盘空间），排除因资源耗尽导致 builder 被终止的可能。
3. 确认该 PR 的 CI 运行失败次数：若仅发生一次，大概率是瞬时 infra 故障；若多次重现，需深入排查 builder 稳定性。
