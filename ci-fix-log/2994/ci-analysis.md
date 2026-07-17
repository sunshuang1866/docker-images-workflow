# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器优雅终止
- 新模式症状关键词: graceful_stop, no builder found, closing transport due to: connection error, rpc error

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`，即 `dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel` 执行过程中
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 DNF 包安装时被优雅终止（GOAWAY 帧 `debug_data: "graceful_stop"`），导致 RPC 连接断开，后续尝试访问该 builder 时回报 `no builder found`。此为 CI 基础设施层面问题，与 PR 代码变更无关。

### 与 PR 变更的关联
**无关**。PR 仅新增了一个标准的 Dockerfile（安装基础编译工具 → 编译安装 Python 3.9.19 → pip 安装 scann）以及对应的 README / meta.yml / image-info.yml 元数据文件。Dockerfile 的前几行（`dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`）是该仓库中最常见、被数百个其他 Dockerfile 使用的基础包安装命令，不存在语法错误或逻辑问题。构建在进行到 DNF 下载元数据阶段（约 39 秒）时，BuildKit builder 被外部机制关闭，属于基础设施故障。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。BuildKit builder 优雅终止（`graceful_stop`）通常由以下原因之一导致：
- builder 所在节点资源不足（内存/磁盘耗尽触发 OOM killer 或节点驱逐）
- builder 实例因节点维护/缩容被调度系统主动回收
- builder 命中了 pod/容器级别的存活时间限制

PR 代码本身无问题，仅需在基础设施稳定后重新运行 CI 流水线。若重试后仍然失败，需由 CI 运维团队排查 `euler_builder_*` 实例所在节点的资源状况。

## 需要进一步确认的点
- 无需进一步确认。错误信息明确指向 BuildKit builder 实例在外部被终止，PR 代码变更未进入实际编译/安装阶段即已中断，不存在代码层面的根因。
