# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 被中止
- 新模式症状关键词: graceful_stop, closing transport, no builder found, rpc error: code = Unavailable, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4]`（`dnf install` 阶段）
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在构建过程中被优雅关闭（`graceful_stop`），导致客户端连接断开，后续无法找到该 builder。这是 CI 基础设施层面的问题，与 PR 代码变更无关。

### 与 PR 变更的关联
**无关**。该 PR 仅新增了一个标准的 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`（包含 `dnf install` 编译工具链、编译安装 Python 3.9.19、pip 安装 scann），以及配套的 `meta.yml`、`README.md`、`image-info.yml` 更新。构建在 `dnf install` 阶段中断，而该阶段尚未执行到任何与本次 PR 新增内容相关的定制逻辑（如 Python 编译或 pip 安装）。

构建日志显示步骤 #1-#6 均已成功完成（加载 Dockerfile、拉取基础镜像 `openeuler/openeuler:24.03-lts-sp4`），步骤 #7 在执行 `dnf install` 过程中 builder 被外部关闭。`dnf install` 命令本身语法和包名均正确，无任何与 Dockerfile 内容相关的报错。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI job**。该失败为 BuildKit builder 实例被意外关闭导致的 `infra-error`，PR 代码本身无问题。直接重新触发 CI 构建即可。

### 方向 2（置信度: 低）
如果多次重试均在同一阶段失败，可能是 CI runner 上 BuildKit daemon 自身存在稳定性问题或资源不足，需联系 CI 基础设施团队检查 runner 节点状态。

## 需要进一步确认的点

1. CI runner `ecs-build-docker-x86-hk` 上 BuildKit daemon（`moby/buildkit:buildx-stable-1`）是否发生了重启或资源回收，导致 builder 被 `graceful_stop`。
2. 该 runner 在相同时间段的其他构建 job 是否也出现同类 builder 断开错误，以确认是否为节点级别的稳定性问题。
3. `dnf install` 下载速度仅 77 kB/s，是否有网络波动导致 builder 被判定为无响应而被超时机制终止。
