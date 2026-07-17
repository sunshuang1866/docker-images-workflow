# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器异常终止
- 新模式症状关键词: graceful_stop, no builder, closing transport, rpc error, Unavailable, euler_builder, docker-container driver

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建第 2/4 步（`dnf install` 步骤），在下载仓库元数据过程中
- 失败原因: BuildKit 构建器 `euler_builder_20260709_224657` 在构建过程中被优雅终止（`graceful_stop`），导致 Docker 客户端与 buildkitd 之间的 gRPC 连接断开，构建中断。该问题属于 CI 基础设施异常，与本次 PR 的代码变更无关。

### 与 PR 变更的关联
无关。本次 PR 仅新增了 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 以及相应的 README、image-info.yml、meta.yml 更新，均为常规的镜像版本新增操作。构建失败发生在 `dnf install` 系统包安装阶段（下载 openEuler 24.03-lts-sp4 基础镜像的仓库元数据时），尚未执行到 Dockerfile 中任何项目特定的 `RUN` 指令，失败原因完全由 CI 基础设施侧 BuildKit 构建器异常终止导致。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。该失败为 BuildKit 构建器意外终止，属于不可复现的 CI 基础设施不稳定问题。无需修改任何代码，重新触发 CI pipeline 即可。如果反复出现，需联系 CI 运维团队排查 BuildKit builder 的稳定性（如是否存在内存/磁盘资源不足、构建器超时自动回收、节点维护等）。

## 需要进一步确认的点
- 日志中 dnf 下载仓库元数据耗时 38 秒以上（77 kB/s，较慢），建议确认 CI 构建节点到 openEuler 仓库的网络状况是否稳定，不稳定的网络可能导致 buildkitd 因心跳超时被编排层终止。
- 如需排除网络因素，可查看同一时间段其他 PR 的 x86-64 构建 job 是否也出现类似问题。

## 修复验证要求
不适用。本失败为 infra-error，无需对代码做任何修改。
