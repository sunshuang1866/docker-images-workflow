# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器断连
- 新模式症状关键词: builder not found, graceful_stop, rpc error, connection error, goaway, Unavailable

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Dockerfile 第 7 行 `RUN dnf install` 步骤（`dnf` 正在下载 OS 元数据时）
- 失败原因: Docker buildx 构建器实例 `euler_builder_20260709_224657` 在构建中途被意外终止（`graceful_stop`），BuildKit 客户端失去与构建器的 gRPC 连接（`rpc error: Unavailable`，`connection error: EOF`），导致后续所有操作报 `no builder found`。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 新增的是一个标准的 scann Dockerfile（安装 gcc/gcc-c++/make/wget/openssl-devel/bzip2-devel/zlib-devel 等基础构建工具 + 编译 Python 3.9.19 + pip install scann），Dockerfile 本身不存在语法错误或异常操作。失败发生在 `dnf install` 下载元数据阶段，此时尚未执行到任何 PR 特有的逻辑（如 Python 编译或 pip install scann）。构建器 `graceful_stop` 表明这是 CI 基础设施侧的主动终止行为（如节点资源回收、超时清理、或底层容器运行时重启），与代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 运行**。该失败为 BuildKit 构建器被基础设施侧主动终止（`graceful_stop`）导致的瞬时 infra-error，非代码问题。直接重新触发 CI（rerun/retry）即可，大概率通过。

### 方向 2（置信度: 低）
若重试后仍然相同位置失败，需排查 CI 构建节点是否有资源限制（磁盘空间不足、内存 OOM、或构建超时策略），该方向无需修改 Dockerfile。

## 需要进一步确认的点
- 构建节点 `ecs-build-docker-x86-hk` 在 `2026-07-09 22:46` 前后是否有资源波动或维护操作。
- 若重试多次仍失败，需确认该构建节点的 disk/memory 资源是否充足（`dnf install` 需要下载和安装约数百 MB 的包）。

## 修复验证要求
无需验证（infra-error，与代码无关）。重新触发 CI 即可。
