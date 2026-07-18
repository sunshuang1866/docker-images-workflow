# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 丢失
- 新模式症状关键词: no builder, graceful_stop, closing transport, rpc error, buildx

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker BuildKit 构建阶段，步骤 #7（dnf 安装系统包）
- 失败原因: CI 使用的 `docker-container` 驱动 BuildKit builder（`euler_builder_20260709_224657`）在构建过程中被意外终止，导致 BuildKit 客户端与 builder 之间的 gRPC 连接断开（graceful_stop），后续步骤无法找到该 builder 实例。

### 与 PR 变更的关联
**与 PR 代码变更无关**。PR 新增了一个标准结构的 Dockerfile（安装基础编译工具链、编译 Python 3.9.19、pip 安装 scann），并更新了 README.md、image-info.yml、meta.yml 三个元数据文件。所有文件均为常规 boilerplate 变更，不可能导致 BuildKit builder 崩溃。此外，CI 的镜像规范检查阶段（"The image specification check for releasing on appstore has passed."）已通过，说明元数据格式无误。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。这是 Docker BuildKit builder 因 CI 基础设施不稳定（runner 资源不足、builder 容器被 OOM Killer 终止、网络波动等）而意外断开连接。PR 代码本身无需修改，Code Fixer 无需处理，重新触发 CI 流水线即可。

## 需要进一步确认的点
1. CI runner（`ecs-build-docker-x86-hk`）是否存在资源不足或 OOM 问题导致 builder 容器被终止。
2. 如多次重试后仍出现同类 "no builder" 错误，需排查 BuildKit daemon 或 docker-container driver 在 CI 环境中的稳定性。
