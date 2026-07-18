# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器异常终止
- 新模式症状关键词: graceful_stop, no builder found, closing transport, error reading from server: EOF, rpc error: code = Unavailable

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]` — `RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`
- 失败原因: Docker BuildKit 构建器 `euler_builder_20260709_224657` 在执行 `dnf install` 过程中异常终止（收到 `graceful_stop` 的 GOAWAY 帧后连接断开），导致构建上下文丢失，后续步骤无法继续。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准的 Dockerfile（安装系统依赖、编译 Python 3.9.19、pip 安装 scann），以及对应的 README、image-info.yml、meta.yml 更新。故障发生在最常规的 `dnf install` 系统包安装阶段，此时尚未执行任何与 PR 特定内容相关的操作。`graceful_stop` 和 `no builder found` 是 BuildKit 基础设施层的问题，可能的触发原因包括：
- CI 构建节点（`ecs-build-docker-x86-hk`）被调度器回收或重启
- BuildKit daemon 因资源限制被 OOM killer 终止
- 网络抖动导致与远程 builder 的长连接中断

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重新触发 CI 即可。** 这是 BuildKit 基础设施层面的临时故障，属于偶发性构建器异常终止，与 Dockerfile 内容无关。建议在 CI 系统中重新跑一次该 PR 的构建流水线。

## 需要进一步确认的点
- 检查 `ecs-build-docker-x86-hk` 节点在对应时段是否有资源耗尽、OOM 或节点回收事件。
- 若重试后仍然失败，需排查 `euler_builder` 实例的稳定性（是否为该节点上并发构建过多导致 BuildKit daemon 过载）。
- 确认 `dnf` 下载的镜像源（日志中显示为 `OS` 仓库）在构建时段是否可达、速度是否正常（77 kB/s 偏慢，可能触发超时）。

## 修复验证要求
（不适用——本次失败为 infra-error，无需修改代码。）
