# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit优雅终止
- 新模式症状关键词: graceful_stop, GOAWAY, no builder found, Unavailable, error reading from server: EOF

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker BuildKit 构建引擎，Dockerfile 第 1 个 `RUN dnf install` 步骤执行期间
- 失败原因: BuildKit 守护进程（builder `euler_builder_20260709_224657`）在执行 `dnf install` 下载仓库元数据时收到 `graceful_stop` GOAWAY 帧，被 CI 基础设施主动终止。客户端随后无法找到已销毁的 builder，构建失败。

### 与 PR 变更的关联
**无关联。** PR 改动仅新增一个 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 及配套文档更新。Dockerfile 内容为标准 `dnf install` 构建依赖 → 编译安装 Python → pip 安装 scann 的流程，语法与依赖声明均无问题。构建失败发生在 `dnf install` 下载元数据的网络 I/O 阶段，BuildKit 守护进程被 CI 编排层主动终止，属于基础设施事件，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 中）
**重新触发 CI 构建。** 此次失败属于 BuildKit 构建守护进程被 CI 编排层意外终止的暂时性基础设施问题。可能的原因包括：构建节点资源回收、调度器超时回收、或 BuildKit 守护进程自身异常退出。通常重新触发 CI 即可恢复。

### 方向 2（置信度: 低）
如果多次重试仍出现相同错误，需检查 CI 构建节点的资源配置（内存/磁盘是否耗尽）、BuildKit 版本兼容性、或构建超时配置是否过短（2.8 MB 以 77 kB/s 下载 37 秒仍在进行中，若超时阈值设置过低可能被误杀）。

## 需要进一步确认的点
- CI 构建节点（`ecs-build-docker-x86-hk`）在失败时间点是否存在资源压力或节点回收事件
- BuildKit 守护进程被 `graceful_stop` 终止的触发原因（超时、资源限制、调度器干预）
- 该失败是否在多架构构建任务（如 x86-64 和 aarch64）中同时出现
