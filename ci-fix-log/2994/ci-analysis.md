# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建连接中断
- 新模式症状关键词: `graceful_stop`, `error reading from server: EOF`, `closing transport`, `no builder "euler_builder_*" found`

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 #7（`dnf install` 阶段）
- 失败原因: BuildKit builder（`euler_builder_20260709_224657`）在 dnf 下载元数据期间被关闭/崩溃，gRPC 连接收到 `graceful_stop` 信号后断开，导致构建中断

### 与 PR 变更的关联
PR 变更与 CI 失败**无关**。本次 PR 新增的 `Dockerfile` 结构正确（安装编译依赖 → 编译 Python 3.9.19 → pip 安装 scann），`meta.yml`、`image-info.yml` 和 `README.md` 的更新也符合项目规范。失败纯粹是因为 CI 基础设施中的 BuildKit builder 实例在构建过程中被意外终止，属于运行环境的瞬时故障，并非代码问题。即便是一个完全正确的 Dockerfile，在 builder 崩溃的条件下也无法构建成功。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。该失败为 infra-error（BuildKit builder 被 `graceful_stop` 终止），与 PR 代码变更无关，无需修改任何文件。Code Fixer 无需处理。

## 需要进一步确认的点
（无——日志清晰显示为基础设施层面的 BuildKit gRPC 连接中断，证据充分，无需进一步确认）
