# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit 构建器异常终止
- 新模式症状关键词: closing transport, error reading from server: EOF, graceful_stop, no builder found

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker BuildKit 构建器运行时阶段（`#7 [2/4] RUN dnf install -y ...` 执行期间）
- 失败原因: Docker BuildKit 构建器 `euler_builder_20260709_224657` 在执行 `dnf install` 步骤（#7 进行到 38.59 秒时）被异常终止，连接断开后构建器实例已不可用。`goaway` 帧中的 `graceful_stop` 提示构建器是被主动关闭（非代码错误触发），属于 CI 基础设施层面的问题。

### 与 PR 变更的关联
**与 PR 变更无关。** 此次 PR 新增的 Dockerfile（`Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`）在语法和逻辑上没有错误。Docker 构建已成功拉取基础镜像（#6 DONE），`dnf install` 步骤正在进行 repo 元数据下载时，BuildKit 构建器会话因基础设施原因断开。Dockerfile 本身不存在导致构建器崩溃的问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修改，触发重试即可。** 这是 CI 基础设施的瞬态故障（BuildKit 构建器会话异常断开），与 PR 代码变更无关。重新触发 CI 流水线大概率可通过。

### 方向 2（置信度: 低）
若多次重试仍失败，需检查 CI runner 节点的磁盘空间和内存资源是否充足。`dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel` 安装大量编译工具链和 -devel 包，可能触发资源限制导致构建器被 OOM Killer 终止。此时需要运维侧调整 CI runner 资源配置，否则可考虑拆分 `dnf install` 步骤减少单次安装的包数量。

## 需要进一步确认的点
- 若重试后仍然失败，需从 CI runner 宿主机日志确认是否存在 OOM Kill、磁盘满、网络超时等资源问题
- 确认 `euler_builder` 构建器是否有超时限制（当前 #7 步骤在 38.59 秒时中断，dnf 元数据下载速度仅 77 kB/s，异常缓慢）

## 修复验证要求
无。该失败类型为 infra-error，Code Fixer 无需处理。若 CI 运维人员确认资源问题已修复或重试后通过，即视为处理完成。
