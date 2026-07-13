# CI 失败分析报告

## 基本信息
- PR: #3014 — chore(3dslicer): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: "构建节点通道断开"
- 新模式症状关键词: ChannelClosedException, EOFException, Unexpected termination of the channel, ecs-build-docker, output clipped, log limit

## 根因分析

### 直接错误
```
#14 4262.5 [ 95%] Building CXX object Modules/IO/MeshBase/src/CMakeFiles/ITKIOMeshBase.dir/itkMeshFileWriterException.cxx.o
#14 4529.2 [output clipped, log limit 2MiB reached]
FATAL: command execution failed
java.io.EOFException
Caused: java.io.IOException: Unexpected termination of the channel
Caused: hudson.remoting.ChannelClosedException: Channel "hudson.remoting.Channel@24d4cc0d:ecs-build-docker-x86-hk": Remote call on ecs-build-docker-x86-hk failed. The channel is closing down or has closed down
FATAL: Unable to delete script file /tmp/jenkins7496920232576494111.sh
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: Jenkins 构建节点 `ecs-build-docker-x86-hk`（x86-64 架构）
- 失败原因: Docker 构建在编译 3D Slicer 源码（ITK 模块约 95% 进度）时，Jenkins agent 与 master 之间的 remoting channel 意外断开，导致构建步骤被标记为失败。日志在约 4530 秒（75 分钟）处因达到 2MiB 限制被截断，此后 channel 中断。

### 与 PR 变更的关联
**高度相关**。PR #3014 新增了 3D Slicer 5.8.1 的完整 Docker 构建流程。Dockerfile 通过 `build-Slicer.sh` 从 GitHub 克隆 Slicer 源码并执行 `cmake --build`，这是一个编译范围极广的 C++ 工程，涉及 VTK、ITK、GDCM、VNL、Qt5 等数十个大型第三方库。日志显示编译过程产生了海量输出（2MiB 日志截断），其中包含大量 `-Wdeprecated-declarations` 警告（QLocale 枚举在 openEuler 2403 搭载的 Qt5 中已标记为废弃），这些警告输出占用了大量日志缓冲区。channel 断开最可能的原因是该 Docker 构建任务在 Jenkins agent 上触发了资源耗尽（推测为 OOM 或磁盘满），导致 agent 进程被系统 kill。

## 修复方向

### 方向 1（置信度: 中）
**构建节点资源不足导致 agent 进程被 OOM kill 或磁盘满**。

该 Docker 构建编译 3D Slicer 及其依赖（VTK、ITK、Qt5 Python bindings 等），是非常重量级的 C++ 编译任务。日志在约 75 分钟、编译进度约 95% 时因 channel 断开而失败——临近链接阶段（link 阶段内存消耗最高），agent 可能因 OOM 被系统 kill。修复思路：
- 检查 Jenkins agent `ecs-build-docker-x86-hk` 的资源配额（内存、磁盘），确认是否需要扩容
- 在 `build-Slicer.sh` 的 cmake 参数中增加 `-DCMAKE_CXX_FLAGS="-Wno-deprecated-declarations"` 以抑制海量 Qt5 废弃 API 警告，减少日志输出量，降低 agent 侧的 IO/内存压力
- 考虑减少并行编译核心数（当前使用 `$(nproc)` 全核心编译），可加 `--parallel $((NUMBER_OF_PHYSICAL_CORES / 2))` 限制

### 方向 2（置信度: 低）
**Docker 构建超时**。

日志显示构建持续约 75 分钟后断开，可能是 Jenkins agent 或 Docker 构建步骤有超时限制。修复思路：
- 检查 Jenkins job 的构建超时设置，必要时调大
- 考虑启用 Docker BuildKit 的缓存功能，将依赖库单独构建为一层以便缓存复用

## 需要进一步确认的点
1. 需要获取 Jenkins agent `ecs-build-docker-x86-hk` 的系统日志（OOM killer 日志 `dmesg`），确认进程是否被 OOM kill
2. 需要确认 agent 节点的内存和磁盘配额是否足以支持 3D Slicer 完整编译（Slicer + VTK + ITK 全量编译预计需要 16GB+ 内存）
3. 需要确认该 agent 上是否同时运行了其他构建任务导致资源争抢
4. 需要确认 arm64 架构（aarch64）的构建 job 是否也以同样方式失败，以判断是否为架构特异性问题
5. 日志被截断在约 4530 秒，实际构建可能在此后继续运行直到 channel 断开，需确认是否有未被捕获的 cmake/gcc 编译错误——当前日志中仅见 deprecation warning，未见 fatal error

## 修复验证要求
若修复方向 1 被采纳（增加编译选项以抑制警告），code-fixer 必须：
1. 在相同 Jenkins agent 上以相同的资源配额触发重试，验证 channel 不再断开
2. 确认构建日志输出量显著减少（不再触发 2MiB 截断）
3. 确认 arm64 构建也能成功完成，而非仅修复 x86-64 单架构
