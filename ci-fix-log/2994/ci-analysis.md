# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器崩溃
- 新模式症状关键词: rpc error, Unavailable, closing transport, EOF, graceful_stop, no builder found

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`，即 `dnf install` 安装编译依赖阶段（gcc、gcc-c++、make、wget、openssl-devel、bzip2-devel、zlib-devel）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行构建过程中被优雅停止（`graceful_stop`），导致 gRPC 连接断开（`error reading from server: EOF`），构建中断。构建器消失后后续状态查询返回 `no builder found`。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 新增了一个标准的 Dockerfile（`Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`），构建尚未到达任何与 Dockerfile 内容相关的关键步骤——失败时仅执行到基础编译依赖的 `dnf install` 阶段，这是所有 Dockerfile 共享的通用操作。构建器 `euler_builder_20260709_224657` 的崩溃属于 CI 基础设施层面的临时故障。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 该失败为 BuildKit 构建器实例意外终止导致的临时性 infra-error，与 PR 代码无任何关联。Code Fixer 无需对 Dockerfile 或任何代码文件做修改。直接重新触发 CI workflow 运行即可，大概率会通过。

## 需要进一步确认的点
- 确认 `euler_builder_20260709_224657` 构建器所在的宿主机（`ecs-build-docker-x86-hk`）在构建期间是否存在资源压力或维护操作导致 builder 被回收。
- 如果多次重试后该构建器仍频繁出现 `graceful_stop`，需要运维侧排查 docker-container driver 和 BuildKit daemon 的稳定性。
