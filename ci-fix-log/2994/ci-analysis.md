# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器异常终止
- 新模式症状关键词: graceful_stop, no builder found, closing transport, EOF, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 [2/4]（第一个 `RUN dnf install` 命令执行期间）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在 Docker 构建过程中被异常终止（`graceful_stop`），导致 gRPC 连接断开（`EOF`），构建进程无法继续。dnf 当时正在下载仓库元数据，尚未进入实际的包安装阶段。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 及相关元数据文件（README.md、doc/image-info.yml、meta.yml）。Dockerfile 内容为常规的 `dnf install` 构建依赖、编译 Python 3.9.19、pip 安装 scann，不存在任何可能导致 BuildKit builder 进程崩溃的代码逻辑。构建甚至未到达 PR 变更特有的步骤（Python 编译、scann 安装），仅在基础镜像拉取后的第一个通用 `dnf install` 阶段即因 builder 实例丢失而失败。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 这是 BuildKit 基础设施层面的瞬时故障（builder 实例被意外停止），与 PR 代码无关。Code Fixer 无需对 Dockerfile 或任何源文件进行修改。建议直接重新触发 CI pipeline，大概率能正常通过。

## 需要进一步确认的点
- 确认 CI 集群中 BuildKit builder 实例的生命周期管理策略——是否存在自动回收 builder 的机制（如空闲超时、资源配额限制），导致构建中的 builder 被误终止。
- 如果重试后仍然失败，需获取 builder 所在宿主机的系统日志（dmesg/journalctl），排查是否存在 OOM killer 或磁盘空间不足导致的 builder 容器被强制停止。

## 修复验证要求
无需验证（infra-error，不涉及代码修改）。
