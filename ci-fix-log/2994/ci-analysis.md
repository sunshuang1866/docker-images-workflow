# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit守护进程被终止
- 新模式症状关键词: graceful_stop, no builder, closing transport, buildx, euler_builder, rpc error, Unavailable

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker BuildKit 基础设施层，非 Dockerfile 代码或构建逻辑内
- 失败原因: BuildKit 守护进程（builder `euler_builder_20260709_224657`）在 Docker 构建第 2/4 步（`dnf install` 下载 metadata 期间，约 38 秒后）被外部信号优雅终止（`graceful_stop`，GOAWAY frame 携带 `NO_ERROR`），导致 buildx 客户端 RPC 连接断开、后续查询 builder 时返回"未找到"。与 PR 的 Dockerfile 变更无关。

### 与 PR 变更的关联
PR 仅新增了 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 及配套的 README、image-info.yml、meta.yml 条目。Dockerfile 内容为标准模式（dnf 安装依赖 → 编译 Python → pip 安装 scann），无语法或逻辑错误。失败发生在 `dnf install` 下载元数据阶段（早于任何编译或 pip 安装），且错误链条完整指向 BuildKit daemon 被外部终止（`graceful_stop`），因此与 PR 代码变更**无关**。

## 修复方向

### 方向 1（置信度: 高）
重新触发 CI 构建。该失败为 CI 基础设施层的 BuildKit 守护进程被意外终止，属于临时性基础设施问题。重新运行相同的 CI job 大概率可成功通过。

## 需要进一步确认的点
- 确认 CI runner（`ecs-build-docker-x86-hk`）上 BuildKit daemon 是否有资源限制（内存/磁盘）或定时回收策略，导致长时间运行的 dnf 下载被终止。
- 如果重新触发后仍然在同一位置失败，需检查 `dnf install` 步骤是否因网络缓慢导致整体构建超时，从而触发了 CI 的 job 超时终止机制。

## 修复验证要求
（无——此失败为 infra-error，无需修改代码或 Dockerfile，重新触发 CI 即可验证。）
