# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: Buildx构建器异常终止
- 新模式症状关键词: graceful_stop, no builder found, rpc error, closing transport, connection error: EOF

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all
#7 38.59 OS   77 kB/s | 2.8 MB  00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`（`dnf install` 下载软件包元数据阶段）
- 失败原因: Buildx 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 期间异常终止（"graceful_stop"），连接断开（gRPC transport 关闭，读 EOF），导致后续构建步骤无法找到该 builder。这属于 CI 基础设施层面问题（构建器容器崩溃/被终止），与 PR 代码变更无关。

### 与 PR 变更的关联
PR 变更完全为增量操作——新增 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 及更新 README、image-info.yml、meta.yml，无逻辑错误。构建器在 Docker 构建的**第 2 个步骤**（dnf 安装系统依赖）期间崩溃，该步骤仅执行 `dnf install` 基本开发工具包，操作在任何 Dockerfile 中均属常规，无法由 PR 内容触发。崩溃发生在 dnf 元数据下载阶段（38 秒仅下载 2.8 MB，速度 77 kB/s，网络状况异常缓慢），进一步指向 Runner 资源或网络问题，而非构建逻辑缺陷。

## 修复方向

### 方向 1（置信度: 中）
该失败为 CI Runner 基础设施问题——Buildx 构建器容器在构建中途被终止（"graceful_stop" + "closing transport" + "no builder found"）。无需修改 PR 代码。建议：
- 检查运行此构建的 Runner（`ecs-build-docker-x86-hk`）当日的资源状态（内存/磁盘/网络带宽是否异常）。
- 触发重试（retry），看构建器是否能在后续运行中正常完成。

### 方向 2（置信度: 低）
若同一 Runner 上多个此类失败重复出现，可能是 Runner 上 Buildx/docker 守护进程配置问题（如 `--max-parallelism` 过高导致资源争抢，或 gc 策略过于激进清理了正在使用的 builder），需排查 Runner 的 BuildKit 运行配置。

## 需要进一步确认的点
1. **Runner 资源状态**：构建日 Runner `ecs-build-docker-x86-hk` 的 CPU/内存/磁盘水位线，以及是否出现了 OOM Kill 事件。
2. **网络质量**：dnf 元数据下载仅 2.8 MB 却耗时 38 秒（77 kB/s），需确认 Runner 到 openEuler 仓库的网络链路是否正常。
3. **重试结果**：触发同一构建的重试，观察是否能正常通过——若重试成功，确认属于偶发性基础设施故障。
4. **下游架构构建 job 日志**：当前日志来自 x86-64 job，日志末尾为 `Finished: FAILURE`（非 SUCCESS），日志中包含完整的构建层错误信息，本次分析不涉及其它下游架构构建 job 日志缺失问题。
