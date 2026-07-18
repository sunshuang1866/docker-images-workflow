# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器异常终止
- 新模式症状关键词: graceful_stop, no builder, closing transport, rpc error, Unavailable, goaway, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 [2/4] `RUN dnf install ...`，约运行 38.59 秒时
- 失败原因: BuildKit 构建器 `euler_builder_20260709_224657` 在 `dnf install` 下载仓库元数据过程中被 CI 基础设施侧主动关闭（`graceful_stop` goaway 帧），导致 Docker 客户端失去与构建器的连接，构建中断。`dnf` 下载速度仅 77 kB/s，疑似慢速网络触发 CI 侧超时机制。

### 与 PR 变更的关联
- **与 PR 代码变更无关**。PR 仅新增了一个结构正确的 Dockerfile（`Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`）及配套的 README.md、image-info.yml、meta.yml 更新。构建失败发生在 `dnf install` 下载系统包阶段，该阶段的行为完全由 CI 基础设施网络状况和超时策略决定，不受 Dockerfile 内容影响。
- 该 Dockerfile 是全新版本（24.03-lts-sp4），CI 需要从零开始构建（无缓存），`dnf install` 需从远程仓库下载约数百 MB 的编译工具链包。在 CI 网络缓慢（77 kB/s）的情况下，单步运行时间可能超过基础设施设置的超时阈值，导致构建器被终止。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施层面：检查 Jenkins agent 节点 `ecs-build-docker-x86-hk` 的网络状况、BuildKit 构建器超时配置（timeout/tcp keepalive），以及 `euler_builder` 的生命周期管理策略。若超时阈值过低，适当调高；若节点到 openEuler 仓库网络持续不达标，排查网络链路或换用其他构建节点重试。

### 方向 2（置信度: 低）
若确认不是基础设施偶发故障，而是该 Dockerfile 构建时间必然超时，可考虑在 Dockerfile 中将 `dnf install` 拆分为更小的步骤（如先单独 `dnf install -y gcc gcc-c++ make wget`，再单独安装 `openssl-devel bzip2-devel zlib-devel`），以降低单步执行时间。但从日志看当前问题在于网络下载速度而非包安装本身，拆分步骤无法解决根因。

## 需要进一步确认的点
- CI 构建节点的网络状况是否正常（77 kB/s 明显偏慢，正常的 DNF 下载应在 MB/s 级别）
- BuildKit 构建器的超时/存活检测配置（`idle-timeout`、`keepalive` 等参数）
- 同一 CI 流水线中其他同时期构建 job 是否有类似失败（判断是否为系统性问题）
- 需确认 `openeuler/openeuler:24.03-lts-sp4` 基础镜像中 `dnf` 仓库配置的镜像源地址是否可达、是否可优化为更近的镜像站
