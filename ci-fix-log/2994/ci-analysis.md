# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 被终止
- 新模式症状关键词: graceful_stop, no builder found, rpc error, connection error, EOF

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel` 执行期间
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 过程中被优雅终止（`graceful_stop`），导致与 builder 的连接断开（RPC EOF），构建中断且 builder 已不可恢复。

### 与 PR 变更的关联
与 PR 代码变更无关。PR 仅新增了一个标准的 Dockerfile（安装 Python 3.9.19 后通过 pip 安装 scann 1.4.2）及配套的 README、image-info.yml、meta.yml 更新。构建在基础镜像拉取成功后、执行 `dnf install` 系统依赖时被 CI 基础设施中断，Dockerfile 语法、内容均无问题。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题，无需修改 PR 代码。重新触发 CI 构建即可（`dnf install` 步骤耗时较长可能触发 builder 超时自动回收，重试时若网络状况较好应能顺利通过）。Code Fixer 无需处理。

## 需要进一步确认的点
- BuildKit builder 被 `graceful_stop` 的具体原因：可能是 CI 流水线的 builder 租约超时（`dnf install` 已运行 38 秒且仍在下载元数据），也可能是 builder 节点资源回收策略触发。
- 建议确认 CI 平台 builder 的超时配置，若 `dnf install` 在海外网络环境下确实耗时过长（日志显示下载速率仅 77 kB/s），可考虑在 Dockerfile 中配置国内镜像源加速。
