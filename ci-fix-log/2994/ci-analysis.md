# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit builder终止
- 新模式症状关键词: graceful_stop, no builder, closing transport, buildx, rpc error, Unavailable

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker buildx 步骤 #7 `[2/4] RUN dnf install ...`（Dockerfile 第 12-15 行对应的第一个 `RUN` 指令）
- 失败原因: Docker buildx builder 容器 `euler_builder_20260709_224657` 在 `dnf install` 下载 OS 元数据期间被终止。gRPC 层收到 `NO_ERROR` GOAWAY 帧携 `graceful_stop` 调试数据，表明 builder 被主动/优雅停止；停止后客户端无法再找到该 builder。构建实际未完成，未发生任何编译或代码层面的错误。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了一个标准结构的新平台 Dockerfile（安装 gcc/gcc-c++/make/wget/openssl-devel/bzip2-devel/zlib-devel，编译 Python 3.9.19，然后 pip 安装 scann 1.4.2）及配套的 README、image-info.yml、meta.yml 更新。所安装的系统包均为 openEuler 仓库标准包，Dockerfile 内容与同项目其他 scann 版本 Dockerfile 结构一致。失败发生在首个 `RUN` 指令中下载 dnf 元数据阶段，远在任何 PR 特有逻辑执行之前，属于 CI 构建基础设施层面的中断。

## 修复方向

### 方向 1（置信度: 中）
**重新触发 CI 运行**。此为构建基础设施层面的瞬时故障（builder 容器被终止），PR 代码本身无误。重新触发相同的 CI job 大概率可以正常通过。建议在重试前检查 CI runner 节点的磁盘空间和内存资源是否充足，以及 buildx builder 是否有显式的生命周期限制（如空闲超时）。

### 方向 2（置信度: 低）
**检查 dnf 元数据下载速度慢是否导致超时**。日志显示 dnf 下载 `OS` 仓库元数据时速度仅 77 kB/s（2.8 MB 耗时 37 秒），若 CI 平台对单一 Docker 构建步骤设有严格的超时限制，缓慢的 dnf 下载可能触发超时进而导致 builder 被终止。可考虑在 Dockerfile 的 `dnf install` 前添加 `dnf makecache` 预热本地缓存，或在 dnf 配置中启用 `fastestmirror` 和 `max_parallel_downloads` 加速下载。

## 需要进一步确认的点
- CI runner 节点 `ecs-build-docker-x86-hk` 在构建当时是否存在资源不足（磁盘/内存/进程数）的情况
- buildx builder `euler_builder_20260709_224657` 的生命周期管理策略：是否存在显式的空闲超时、最大构建时长限制，或是否有其他并发 job 对其执行了清理操作
- dnf 元数据下载耗时 37 秒是否触发了某个 CI 层面的超时阈值
- 同一时间段内，其他 PR 的 x86-64 构建 job 是否也出现类似失败（以判断是全局基础设施问题还是单次偶发故障）
