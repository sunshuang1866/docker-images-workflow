# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器异常终止
- 新模式症状关键词: graceful_stop, reading from server: EOF, no builder found, buildkit, closing transport

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建的 `RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all` 步骤（Dockerfile 第 7 行对应区域）
- 失败原因: BuildKit 构建器实例在 dnf 拉取仓库元数据过程中被异常终止（goaway 帧 debug data 为 `graceful_stop`），gRPC 连接断开，后续步骤无法继续执行。

### 与 PR 变更的关联
**与 PR 改动无关**。该失败发生在 BuildKit 构建器的底层通信层，属于 CI 基础设施层面的异常。PR 仅新增了一个标准的 Dockerfile（安装基础编译工具链 + 源码编译 Python 3.9.19 + pip 安装 scann），无语法错误或异常操作。构建在 dnf 下载仓库元数据阶段停滞 38+ 秒（下载速率仅 77 kB/s），之后 BuildKit builder 容器被终止，推测是由于构建节点资源回收、超时或 builder 容器被外部管理进程关闭所致。

## 修复方向

### 方向 1（置信度: 中）
**重新触发 CI 构建**。该失败属于 CI 基础设施偶然性故障（BuildKit builder 异常终止），未发现 Dockerfile 或 PR 代码层面的问题。直接对同一 PR 重新运行 CI pipeline 大概率可以成功通过。

### 方向 2（置信度: 低）
若重试仍然失败且同一 builder 继续异常终止，需联系 CI 基础设施团队排查 `ecs-build-docker-x86-hk` 构建节点的 BuildKit 实例稳定性，检查是否存在 builder 资源配额不足、内存耗尽或节点自动回收策略触发阈值过低等问题。

## 需要进一步确认的点
- CI 构建节点的 BuildKit daemon 日志，确认 `euler_builder_20260709_224657` 实例被终止的具体原因（OOM Kill？超时回收？手动清理？）
- dnf 元数据下载速度仅 77 kB/s（正常应 >1 MB/s），确认 `ecs-build-docker-x86-hk` 节点到 docker.io 和 openEuler 镜像源之间的网络质量是否正常
- 同一时间段其他 PR 是否也出现类似 BuildKit 连接断开错误，以判断是个例还是系统性问题
