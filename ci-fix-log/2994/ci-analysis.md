# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器被终止
- 新模式症状关键词: failed to receive status, rpc error, closing transport, goaway, graceful_stop, no builder found

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker build 步骤 `#7 [2/4]`（`dnf install` 阶段），约开始后 38.59 秒
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在 `dnf install` 下载 OS 仓库元数据过程中被**优雅终止**（`goaway: code: NO_ERROR, debug data: "graceful_stop"`），导致 gRPC 传输层关闭（EOF），随后该 builder 已不可用（"no builder found"）。构建器被终止前，Docker build 的前 6 个步骤（拉取 base 镜像 `openeuler/openeuler:24.03-lts-sp4`）均正常完成。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 语法正确、依赖声明完整，dnf 包列表（`gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`）均为 openEuler 仓库中的标准包。构建器在下载仓库元数据阶段被终止，尚未进入实际安装或编译阶段，属于 CI 基础设施层面的问题。PR 的其他变更（README.md、image-info.yml、meta.yml）均为纯文本/元数据更新，不参与构建过程。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 此为 BuildKit 构建器实例被基础设施层回收/终止导致的瞬态故障，非代码问题。直接 re-run 失败的 job 即可。如果反复出现，需排查 CI runner 节点的资源配额（内存/磁盘）或构建器实例的生命周期策略。

## 需要进一步确认的点
- 如果多次 re-run 仍失败，需检查 `ecs-build-docker-x86-hk` 节点的资源状况和 BuildKit 构建器池的可用性。
- 确认 `openeuler/openeuler:24.03-lts-sp4` 基础镜像的 dnf 仓库元数据是否响应过慢（日志显示 37 秒仅完成 metadata 下载，后续实际包安装尚未开始）。
