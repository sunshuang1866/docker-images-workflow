# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器崩溃
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
- 失败位置: Docker 构建阶段 Step #7（`dnf install` 下载仓库元数据期间）
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在执行 `dnf install` 时突然断开连接（`graceful_stop`），导致客户端收到 `rpc error: closing transport`，构建进程中断。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了一个标准 Dockerfile（安装 gcc/gcc-c++/make/wget + openssl-devel/bzip2-devel/zlib-devel → 编译 Python 3.9.19 → pip 安装 scann），以及配套的 README、image-info.yml、meta.yml 条目。Dockerfile 内容没有语法错误、无效命令或异常操作，`dnf install` 的包列表均为 openEuler 24.03 仓库中合法存在的包。失败是 BuildKit builder 进程在 `dnf install` 下载元数据阶段异常退出所致，属于 CI 基础设施层面的问题。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。这是一个 BuildKit builder 进程异常崩溃的 infra-error，与代码无关。建议在 Jenkins 中重新运行该 job（或通过 commit --amend / 空 commit 重新触发），大概率可以正常通过。

### 方向 2（置信度: 低）
如果反复重试仍然失败且均发生在 `dnf install` 阶段，可能是 CI runner（`ecs-build-docker-x86-hk`）的磁盘空间不足或内存不足导致 BuildKit 容器被 OOM Killer 杀死。此时需联系 CI 基础设施团队排查 runner 资源状态。

## 需要进一步确认的点
- CI runner `ecs-build-docker-x86-hk` 在构建时间（2026-07-09 22:46 UTC）的磁盘/内存使用情况，确认是否因资源耗尽导致 BuildKit builder 容器被终止。
- BuildKit builder 容器是否有 OOM kill 日志（可通过 `dmesg` 或容器运行时日志确认）。
