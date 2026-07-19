# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器中断
- 新模式症状关键词: graceful_stop, closing transport, error reading from server: EOF, no builder found, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4]`（`dnf install` 执行期间）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 过程中被优雅关闭（`graceful_stop`），导致传输层连接断开（EOF），随后构建器实例已不可用（`no builder found`）。这是 CI 基础设施层面的故障，与 PR 的代码变更无关。

### 与 PR 变更的关联
PR 变更为新增 scann 1.4.2 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 内容为标准模式（安装编译依赖 → 编译 Python → pip 安装 scann），`dnf install` 安装的包（gcc、gcc-c++、make、wget、openssl-devel、bzip2-devel、zlib-devel）均为 openEuler 仓库中的常规包，不存在拼写错误或不存在的包名。

构建失败发生在 `dnf install` 下载元数据阶段（运行约 39 秒，下载速度仅 77 kB/s），尚未进入包的安装或后续 Python 编译阶段。BuildKit 构建器实例被关闭（`graceful_stop`）属于 CI 节点资源回收或构建器守护进程异常，与 Dockerfile 内容无因果关系。

## 修复方向

### 方向 1（置信度: 中）
**触发 CI 重试。** 该失败属于 CI 基础设施问题（BuildKit 构建器被意外终止），非代码层面错误。同一 PR 在其他架构节点（如 aarch64）上可能构建成功。直接重新触发 CI pipeline（re-run）即可验证。

### 方向 2（置信度: 低）
如果多次重试仍然在同一位置失败，且始终表现为 `dnf install` 阶段耗时过长（下载速度极慢），可能与 CI 构建节点到 openEuler 仓库的网络连接质量有关。此时需由 CI 运维排查构建节点（`ecs-build-docker-x86-hk`）的网络状况，而非修改 Dockerfile。

## 需要进一步确认的点
1. 该 PR 在 aarch64 架构 job（`/job/aarch64/…`）上的构建结果如何？如果 aarch64 构建成功，则进一步证实 x86-64 节点上的失败是孤立的基础设施事件。
2. x86-64 构建节点 `ecs-build-docker-x86-hk` 在同一时间段是否有其他 job 也出现 BuildKit 构建器中断？如果普遍存在，说明节点或 BuildKit 服务存在问题。
3. `dnf install` 下载元数据仅 77 kB/s 的速率是否正常？如果该节点持续如此，可能是网络带宽被其他并发 job 耗尽或仓库镜像站限速。

## 修复验证要求
无需特殊验证。本 PR 的失败为 infra-error，无需修改代码。CI 重试后若构建通过即可合入。
