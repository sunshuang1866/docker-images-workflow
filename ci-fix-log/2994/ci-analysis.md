# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 构建器意外终止
- 新模式症状关键词: graceful_stop, no builder found, closing transport, rpc error, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建第 7 层（Dockerfile 第 8-9 行 `RUN dnf install -y ... && dnf clean all`）
- 失败原因: CI 基础设施中的 BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 命令过程中被外部发送 `graceful_stop` 信号强制终止，导致构建连接断开，与 PR 代码变更无关。

### 与 PR 变更的关联
PR 新增了一个全新的 Dockerfile（`Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`），这是标准的镜像新增流程，Dockerfile 内容本身无明显错误。`dnf install` 步骤正在正常下载元数据（已下载 38.59 MB）时构建器被外部终止，属于 CI 基础设施异常，非 PR 代码问题。

## 修复方向

### 方向 1（置信度: 高）
**不需要修改 PR 代码。** 该失败是 CI 基础设施问题——BuildKit 构建器容器在构建过程中被强制停止。应重新触发 CI 构建（re-run），如果反复出现则需要排查 Jenkins 节点资源、构建超时配置或 Docker daemon 稳定性。

## 需要进一步确认的点
- 同一 CI 节点上是否有其他并发构建触发了资源争抢导致构建器被驱逐
- BuildKit 构建器 `euler_builder_20260709_224657` 的停止是超时触发还是手动/自动运维操作
- 该节点是否有磁盘空间、内存不足等资源告警
