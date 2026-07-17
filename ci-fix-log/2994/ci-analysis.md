# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit 构建器被终止
- 新模式症状关键词: `graceful_stop`, `closing transport`, `no builder found`, `rpc error: code = Unavailable`

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker build 步骤 #7（`dnf install` 下载 openEuler 包仓库元数据阶段）
- 失败原因: Docker BuildKit 构建器（`euler_builder_20260709_224657`）在执行 `dnf install` 期间被外部因素终止。日志中 `graceful_stop` 和 `NO_ERROR` 表明 BuildKit daemon 收到了干净关闭信号（非崩溃），构建客户端随后失去与构建器的连接，报 gRPC 传输错误。PR 代码变更（新增 scann Dockerfile 及元数据文件）自身无语法或逻辑问题，构建尚未进入 PR 特有的 Python 编译和 pip 安装阶段。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 构建仅在执行 Dockerfile 第一个 `dnf install` 步骤（安装 gcc、openssl-devel 等基础系统包）时失败——这是所有基于 openEuler 镜像构建的通用步骤。构建器的 `graceful_stop` 发生在 OS 仓库元数据下载阶段（仅下载了 2.8 MB 元数据，速度 77 kB/s，耗时约 37 秒），未触及 PR 新增的任何定制逻辑（Python 编译、scann pip 安装）。可能的原因包括：

1. CI runner 上的 BuildKit builder 因资源限制（内存/磁盘不足）被 OOM killer 或容器运行时清理
2. CI 编排层的 job 超时策略触发了 builder 清理
3. CI 基础设施节点上的 builder 实例被外部管理进程回收

## 修复方向

### 方向 1（置信度: 中）
**无需修改 PR 代码**。此失败属于 CI 基础设施问题，建议通过以下方式验证：
- 在 CI 系统中重新触发该 job（retry），观察是否可复现
- 若反复失败，检查 CI runner 节点的资源使用情况（内存、磁盘空间）和 BuildKit builder 的存活时间限制配置
- 检查 CI 编排日志中是否有 job 层面的 timeout 或资源配额触发记录

## 需要进一步确认的点
1. CI runner（`ecs-build-docker-x86-hk`）在构建期间是否发生了 OOM 事件或磁盘空间不足（可查看系统日志 `dmesg` / `journalctl`）
2. BuildKit daemon 的 `graceful_stop` 是 CI 工具链主动触发的（如 job timeout），还是 runner 级别的容器/进程管理器触发的
3. 同一 CI runner 上其他并发构建 job 是否也在相近时段失败（判断是否为节点级故障）
4. 若重试后依然失败，需要获取 BuildKit daemon 自身日志，确认 `graceful_stop` 的触发源头

## 修复验证要求
不适用（infra-error，无需修改代码）。
