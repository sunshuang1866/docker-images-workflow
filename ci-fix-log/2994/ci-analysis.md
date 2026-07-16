# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit 构建器连接丢失
- 新模式症状关键词: `failed to receive status`, `closing transport`, `graceful_stop`, `no builder`, `euler_builder`

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: Docker 构建阶段，第 `#7 [2/4]` 步（`dnf install` 下载系统包元数据时）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在 `dnf install` 执行至 38.59 秒时被优雅关闭（`graceful_stop`），导致 Docker 客户端无法继续接收构建进度，后因构建器已不存在（`no builder found`）而彻底失败。`graceful_stop` 的 GOAWAY 原因码（`NO_ERROR`）表明这是服务端主动发起的关闭，非协议错误。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 新增的 Dockerfile 语法正确，`dnf install` 包列表（gcc、gcc-c++、make、wget、openssl-devel、bzip2-devel、zlib-devel）均为 openEuler 仓库标准可用包。失败发生在基础设施层——BuildKit 构建器在构建过程中被终止，属于 CI 环境问题，非代码缺陷。Dockerfile 中 `dnf install` 命令本身无语法或逻辑错误。

## 修复方向

### 方向 1（置信度: 中）
**CI 基础设施问题，Code Fixer 无需处理。** 建议重新触发 CI 运行（re-run / re-trigger）。若多次重试仍失败，需排查 CI 节点资源状况：
- 构建节点（`ecs-build-docker-x86-hk`）在 `dnf install` 下载期间是否触发 OOM Killer 导致 BuildKit 守护进程被终止
- 是否存在磁盘空间不足导致构建器被清理
- BuildKit 守护进程是否存在自动重启策略或资源配额限制

### 方向 2（置信度: 低）
若多次重试均在同一 `dnf install` 步骤失败，可能是 openEuler 24.03-lts-sp4 基础镜像的 `dnf` 仓库元数据下载量过大导致超时。可考虑在 Dockerfile 中将 `dnf install` 的包列表拆分、或添加 `dnf makecache` 预热步骤。但当前日志证据不足以支持此方向。

## 需要进一步确认的点
1. 是否重试（re-run）后仍然失败？若重试通过，则可确认为 CI 瞬态故障。
2. CI 构建节点（`ecs-build-docker-x86-hk`）的系统日志（`dmesg` / `journalctl`）中是否存在 OOM 或磁盘空间告警。
3. BuildKit 构建器 `euler_builder_20260709_224657` 是否设置了存活时间（TTL）或空闲超时，在 38 秒 `dnf` 下载过程中被定时清理。
4. 同一 CI 节点上并行构建的其他 job 是否可能挤占资源导致本构建器被驱逐。
