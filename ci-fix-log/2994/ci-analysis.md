# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 构建器被终止
- 新模式症状关键词: rpc error, Unavailable, closing transport, graceful_stop, no builder found

## 根因分析

### 直接错误

```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位

- 失败位置: Docker 构建第 [2/4] 步（`dnf install` 下载 OS 仓库元数据阶段）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行期间被上层服务优雅终止（`graceful_stop`），导致 gRPC 连接断开，构建客户端失去与构建器的通信。该错误与 PR 代码变更**无关**，属于 CI 基础设施问题（构建器被回收/重启/资源耗尽等）。

### 与 PR 变更的关联

**无关**。PR 新增了一个语法正确的 Dockerfile（`Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`），以及配套的 README.md、image-info.yml、meta.yml 元数据更新。构建在 `dnf install` 下载仓库元数据阶段因构建器被终止而失败，远在触及任何 scann 相关逻辑之前。Dockerfile 中列出的软件包（`gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`）均为 openEuler 标准仓库中的常见包，不存在包名或版本问题。

## 修复方向

### 方向 1（置信度: 高）
**重试构建**。该失败为 CI 构建器实例被意外终止所致，与代码无关。最直接的修复方式是重新触发 CI 流水线（re-run），等待分配新的健康构建器实例即可通过构建。

### 方向 2（置信度: 低）
如果重试后反复在同一位置失败，需排查构建器所在宿主机的资源状况（内存、磁盘、构建器生命周期配置），但此类操作超出 PR 提交者权限范围，需联系 CI 运维团队处理。

## 需要进一步确认的点

1. 构建器 `euler_builder_20260709_224657` 被 `graceful_stop` 的具体原因——是宿主机资源限制（OOM、磁盘满）、超时策略触发的自动回收、还是运维人员手动操作。
2. `dnf` 下载 OS 仓库元数据时速度仅 77 kB/s（2.8 MB 耗时 37 秒），若构建器有较短的闲置/执行超时配置，慢速网络可能导致构建器在元数据下载期间被判定为超时而终止。需要确认 CI 构建器的超时配置。
3. 建议在重试前确认 `openeuler:24.03-lts-sp4` 基础镜像在 Docker Hub 上的可用性及网络可达性（构建日志中基础镜像拉取成功，但仓库元数据下载速度异常偏慢）。

## 修复验证要求

不适用——本次失败为 infra-error，不涉及代码修复，无需 Code Fixer 处理。
