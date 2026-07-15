# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器异常终止
- 新模式症状关键词: failed to receive status, rpc error, closing transport, grace_stop, no builder found

## 根因分析

### 直接错误
```
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建阶段 `#7 [2/4] RUN dnf install -y ...`（Dockerfile 第 6-8 行）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 期间被异常终止（`graceful_stop`），导致客户端连接断开（`EOF`），后续重连时发现构建器已不存在。日志显示 `dnf` 下载 OS 元数据时速度极慢（77 kB/s，2.8 MB 耗时 37 秒），构建器可能因资源超限或超时被驱逐。

### 与 PR 变更的关联
**与 PR 无关**。PR 的变更仅为：
1. 新增 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`（标准 Dockerfile，安装 dnf 包、编译 Python 3.9.19、pip 安装 scann）
2. 更新 `README.md`、`image-info.yml`、`meta.yml` 添加新镜像条目

Dockerfile 内容无语法或逻辑问题，且构建失败发生在最基础的 `dnf install` 步骤（安装 gcc/gcc-c++/make/wget/openssl-devel/bzip2-devel/zlib-devel），这些均为 openEuler 仓库的标准包，与 PR 引入的代码逻辑无关。

## 修复方向

### 方向 1（置信度: 中）
触发 CI 重试（re-run）。这是典型的 CI 基础设施临时故障——构建器在依赖安装阶段因资源超限或网络抖动导致被终止。PR 代码本身无问题，重试后大概率通过。

### 方向 2（置信度: 低）
若多次重试均在相同位置失败，可能是该 CI runner（`ecs-build-docker-x86-hk`）存在资源不足或网络不稳定问题（如到 openEuler 仓库的连接带宽过窄），需联系 CI 运维团队排查 runner 健康状况。

## 需要进一步确认的点
1. 该 CI runner（`ecs-build-docker-x86-hk`）的磁盘空间、内存是否充足
2. `euler_builder_20260709_224657` 构建器实例的运行日志——是超时被 kill 还是因 OOM 被终止
3. CI 系统中 docker buildx builder 的超时策略配置
4. 该 PR 是否还有其他架构（aarch64）的下游构建 job，其日志是否需要一并检查
