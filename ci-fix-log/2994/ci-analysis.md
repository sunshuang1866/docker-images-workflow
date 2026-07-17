# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 失联
- 新模式症状关键词: failed to receive status, rpc error, closing transport, graceful_stop, no builder found

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`，即 `dnf install` 安装系统编译依赖阶段
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在 `dnf` 下载 OS 仓库元数据（2.8 MB，下载速度仅 77 kB/s，耗时 ~37 秒）过程中意外失联。日志中的 `graceful_stop` 表明 builder 被主动或被动关闭，导致 Docker 构建 RPC 连接中断，构建终止

### 与 PR 变更的关联
**无关**。PR 新增的 Dockerfile 内容为标准的 openEuler 镜像构建流程（安装 gcc/make/wget 等编译工具 → 编译 Python 3.9.19 → pip 安装 scann），DNB 安装命令语法正确、参数有效。构建在 `dnf install` 阶段因 BuildKit builder 连接丢失而崩溃，属于 CI 基础设施层面的问题，与 PR 代码变更无任何关联。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复**。该失败是 CI 基础设施问题（BuildKit builder 意外失联），Code Fixer 不需要对 Dockerfile 或任何源文件做修改。重新触发 CI 构建即可（若 builder 恢复正常，构建预计能成功通过）。

### 方向 2（置信度: 低，备选）
如果该 builder 失联问题在同一个 runner（`ecs-build-docker-x86-hk`）上持续复现，可能需要运维排查该节点的 BuildKit daemon 稳定性、网络连接质量（日志中 77 kB/s 的包下载速度异常偏慢，可能暗示网络瓶颈）或 builder 超时/回收策略。

## 需要进一步确认的点
- 若 CI 重跑后仍然失败在同一位置，需运维确认 `ecs-build-docker-x86-hk` runner 上 BuildKit daemon 的健康状态和资源使用情况
- `dnf` 下载元数据仅 77 kB/s，远低于正常速度，建议确认 runner 到 openEuler 仓库镜像源之间的网络连通性
