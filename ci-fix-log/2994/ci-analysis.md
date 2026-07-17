# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器失联
- 新模式症状关键词: graceful_stop, no builder found, closing transport, error reading from server: EOF

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker BuildKit 构建阶段，`RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all` 执行期间
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在构建过程中被外部终止（graceful_stop），导致客户端与构建器之间的 gRPC 连接断开，后续步骤找不到该构建器实例，构建失败。

### 与 PR 变更的关联
与 PR 变更无关。PR 仅新增了一个标准的 Dockerfile（安装编译依赖、编译 Python 3.9.19、pip 安装 scann）和相应的 README/meta/image-info 元数据文件更新。Dockerfile 内容正常，`dnf install` 步骤正在正常下载元数据（77 kB/s 速率下载 2.8 MB 元数据）时构建器被外部终止，属于 CI 基础设施层面的问题。后两个错误（`graceful_stop` + `no builder found`）均指向 BuildKit 守护进程/容器被 CI 环境回收或异常退出，与 Dockerfile 内容无因果关系。

## 修复方向

### 方向 1（置信度: 高）
手动重试 CI job。此失败为 BuildKit 基础设施瞬时故障（构建器实例被异常终止），Dockerfile 代码无问题。重新触发 CI 构建大概率可以通过。

## 需要进一步确认的点
（无）——日志中错误信息明确指向 BuildKit 基础设施故障（graceful_stop 导致构建器不可用），与代码变更无关联，无需进一步排查。
