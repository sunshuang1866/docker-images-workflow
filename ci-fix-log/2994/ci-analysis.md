# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 异常终止
- 新模式症状关键词: graceful_stop, closing transport, no builder found, buildkit, rpc error

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker build 步骤 `#7 [2/4]`，`dnf install` 命令执行期间
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 下载 openEuler 24.03-LTS-SP4 的 RPM 元数据过程中（约 38 秒后）被异常终止。错误信息中的 `goaway: code: NO_ERROR, debug data: "graceful_stop"` 表明构建器收到了正常的停止信号（可能是节点回收、资源配额触发或调度器主动终止），导致连接中断，随后构建器实例被完全移除，Docker build 无法继续。

### 与 PR 变更的关联
**与 PR 无关。** 本次 PR 新增的 Dockerfile 内容语法正确，CI 的镜像规格预检也已通过（`The image specification check for releasing on appstore has passed`）。构建失败发生在 BuildKit 基础设施层面——构建器实例在 dnf 安装软件包的过程中被外部力量异常终止，属于 CI 运行环境的偶发性不稳定问题，与代码变更无关。`dnf install` 步骤正在正常工作（下载 OS 仓库元数据，速率 77 kB/s），并未出现任何代码逻辑错误或编译失败。

## 修复方向

### 方向 1（置信度: 高）
**无需修复代码。** 这是 CI 基础设施的偶发性问题（BuildKit builder 被异常回收），与 PR 变更无关。建议重新触发 CI 构建，通常重试即可通过。

## 需要进一步确认的点
- 本次 CI 运行所在的节点 `ecs-build-docker-x86-hk` 是否在此期间发生了节点调度变更或资源回收。
- 构建器 `euler_builder_20260709_224657` 的终止原因是否为 CI 平台的资源限制（如构建超时、内存 OOM、磁盘不足等），可通过查看 CI 平台的节点事件日志进一步确认。
