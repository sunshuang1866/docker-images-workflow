# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 构建器连接中断
- 新模式症状关键词: failed to receive status, rpc error, closing transport, EOF, graceful_stop, no builder found, buildx

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker build 步骤 `[2/4] RUN dnf install`（`Others/scann/1.4.2/24.03-lts-sp4/Dockerfile:10-13`）
- 失败原因: Docker buildx 构建器实例 `euler_builder_20260709_224657` 在 `dnf install` 下载元数据过程中（运行约 38 秒后被优雅关闭（graceful_stop），导致 BuildKit RPC 连接断开（EOF），后续无法找到该构建器。

### 与 PR 变更的关联
**与 PR 改动无关**。该失败属于 CI 基础设施问题（BuildKit builder 实例被提前回收/关闭），不是 Dockerfile 代码错误。PR 仅新增了 scann 1.4.2 在 openEuler 24.03-lts-sp4 上的 Dockerfile 和相关元数据文件，Dockerfile 语法和 `dnf install` 命令本身均无问题——基础镜像已成功加载，`dnf install` 在正常下载 RPM 仓库元数据时因构建器连接丢失而中断。

证据：
1. 基础镜像拉取成功（`#6 DONE 2.9s`）
2. CI 元数据预检通过（`The image specification check for releasing on appstore has passed.`）
3. `dnf install` 正在正常下载 OS 仓库元数据（77 kB/s, 已下载 2.8 MB）
4. 错误为 gRPC 传输层错误（`closing transport`, `EOF`, `graceful_stop`），非构建逻辑错误

## 修复方向

### 方向 1（置信度: 高）
**重试 CI**。该失败为 BuildKit builder 实例被意外回收导致的基础设施问题，Dockerfile 本身无错误。直接重新触发 CI pipeline 大概率可成功通过。

## 需要进一步确认的点
- 若重试后仍失败，需检查 CI 环境中 `euler_builder` 实例的生命周期配置（是否有超时自动回收机制），以及构建节点的资源状况（内存/磁盘是否充足）。
- 若重试后在相同步骤（`dnf install`）卡住或超时，可能是 openEuler 24.03-lts-sp4 的 dnf 仓库源在 CI 构建节点上网络访问慢或不可达，需检查网络连通性。
