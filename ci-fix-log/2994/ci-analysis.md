# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 构建器异常关闭
- 新模式症状关键词: gracefull_stop, closing transport, no builder found, rpc error, connection error, BuildKit

## 根因分析

### 直接错误
```
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker build 步骤 `[2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`（dnf 下载元数据阶段）
- 失败原因: BuildKit 构建器 `euler_builder_20260709_224657` 在构建过程中被主动发送 GOAWAY 帧（`graceful_stop`）关闭，导致与 builder 的 RPC 连接断开，后续尝试查找同一 builder 时已不存在。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了一个标准的 Dockerfile（安装 gcc/cmake 等编译工具后通过 pip 安装 scann），以及 README 和 meta.yml 的配套条目更新。Docker build 已成功拉取基础镜像并开始 `dnf install` 步骤，但 BuildKit builder 节点在执行过程中被外部关闭（运维操作、资源回收或节点故障），导致构建中断。没有任何迹象表明 Dockerfile 语法或内容存在错误。

## 修复方向

### 方向 1（置信度: 高）
重新触发 CI 流水线。此为 CI 基础设施问题（BuildKit builder 被 graceful stop），与 PR 代码无关，重试大概率可以通过。

## 需要进一步确认的点
- 无法获知 builder `euler_builder_20260709_224657` 被关闭的具体原因（可能是 CI 节点维护、资源配额回收或节点异常），但这对修复决策无影响——重试即可。
