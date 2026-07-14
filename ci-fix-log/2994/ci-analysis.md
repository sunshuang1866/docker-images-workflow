# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 断连
- 新模式症状关键词: closing transport, connection error, EOF, graceful_stop, no builder found

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Dockerfile Step 2/4（`RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`）
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在 dnf 下载仓库元数据阶段被意外终止（`graceful_stop`），导致构建进程与 builder 的连接断开，dnf install 步骤未能完成。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了一个标准 Dockerfile（安装编译工具链、编译 Python 3.9.19、pip 安装 scann）以及对应的 README、image-info.yml、meta.yml 条目。构建失败发生在 Dockerfile 第一个 `RUN` 指令中——尚未执行任何与 scann 或 Python 编译相关的操作，仅在下载系统软件包仓库元数据时 builder 崩溃。Dockerfile 内容本身无任何异常，失败纯属 CI 基础设施层面的 builder 意外终止。

## 修复方向

### 方向 1（置信度: 高）
**不涉及代码修改，重新触发 CI 构建即可。** 该失败为临时性的 BuildKit builder 实例崩溃/断连问题。类似 "graceful_stop" 的报错通常由 CI 宿主机资源紧张、builder 实例被 scheduler 回收、或网络抖动触发 gRPC 连接重置引起。Code Fixer 无需修改任何文件，直接 re-run CI。

## 需要进一步确认的点
无。日志错误信息明确指向 BuildKit 基础设施故障，与代码变更无关。如果同一 PR 多次触发后均在同一位置失败，则需要排查 CI 基础设施侧（builder 节点资源配额、网络策略等）。

## 修复验证要求
无。该失败为 infra-error，无需任何代码修复。
