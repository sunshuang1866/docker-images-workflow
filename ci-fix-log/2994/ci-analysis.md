# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器断连
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
- 失败位置: Docker 构建步骤 `#7 [2/4]`（`RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在 Docker 构建过程中意外断开连接（gRPC 传输层收到 EOF，goaway 原因为 `graceful_stop`），导致构建无法继续。随后构建器实例已不可用（`no builder ... found`）。dnf 正在下载 2.8MB 的 metadata 时连接断开，并非 dnf 命令本身报错。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个 Dockerfile（`Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`）并更新了配套的元数据文件（README.md、image-info.yml、meta.yml）。Docker 构建在启动后的第二个 `RUN` 指令（安装基础编译工具链）期间因 CI 基础设施的 BuildKit 构建器崩溃而失败，构建本身尚未到达任何可能由 PR 代码内容触发的错误阶段。

## 修复方向

### 方向 1（置信度: 高）
**CI 基础设施问题，无需修改代码。** 这是 BuildKit 构建器（`euler_builder_20260709_224657`）在构建过程中意外终止导致的基础设施故障。建议操作：
- 重新触发 CI job，大概率可成功通过（构建器不稳定通常是一次性事件）
- 若反复复现，需排查 BuildKit builder 所在宿主机的资源状态（内存、磁盘、OOM kill）或网络连通性

## 需要进一步确认的点
（无需进一步确认。错误信息清晰指向 BuildKit builder 的 gRPC 连接被 `graceful_stop` 终止，属于 CI 基础设施层面问题。）
