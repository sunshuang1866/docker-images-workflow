# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 构建器连接丢失
- 新模式症状关键词: `failed to receive status`, `closing transport`, `graceful_stop`, `no builder`, `rpc error`, `Unavailable`

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker BuildKit 构建步骤 `[2/4]` — `dnf install` 执行期间
- 失败原因: Docker BuildKit 构建器实例 `euler_builder_20260709_224657` 在构建过程中被优雅关闭（`graceful_stop`），导致客户端 RPC 连接断开，构建中断。`dnf` 下载仓库元数据耗时 38.59 秒仅完成 2.8MB，下载速率仅 77 kB/s，网络极度缓慢，可能触发了 CI 构建超时或资源限制，导致构建器被终止。

### 与 PR 变更的关联
PR 新增的 Dockerfile 中 `dnf install` 命令本身语法正确、包名有效，不直接导致构建器断连。失败为 CI 基础设施异常（BuildKit 构建器在 `dnf` 元数据下载阶段因网络缓慢/资源超限被终止），与 PR 代码变更无直接因果关系。但 `dnf` 异常缓慢（77 kB/s）可能与 openEuler 24.03-lts-sp4 基础镜像的默认 yum 仓库配置有关，不排除该镜像的仓库源在 CI 环境中网络连通性差。

## 修复方向

### 方向 1（置信度: 低）
**重试构建**。该错误为 infra-error，最直接的方式是触发 CI 重新运行。若重试后通过，则确认为偶发性基础设施故障。

### 方向 2（置信度: 低）
**检查并优化 dnf 仓库源配置**。在 Dockerfile 中，在执行 `dnf install` 前先替换为 CI 环境网络连通性更好的镜像源（如华为云镜像站 `repo.huaweicloud.com`），避免因基础镜像默认仓库源网络缓慢导致 dnf 操作耗时过长触发超时。需对比同类 openEuler 24.03-lts-sp4 的 Dockerfile（如 PR #2896、#2926 等）确认是否已有此类仓库源替换的先例。

## 需要进一步确认的点
1. CI 环境中 Docker BuildKit 构建器的超时配置和资源限制（内存/磁盘），确认 `graceful_stop` 的触发条件。
2. openEuler 24.03-lts-sp4 基础镜像的默认 yum 仓库源在 CI 构建节点上的网络连通性和下载速率，确认 77 kB/s 是否为常态。
3. 同批次是否有其他 24.03-lts-sp4 镜像构建也出现类似 `graceful_stop` 错误，以判断是系统性问题还是个别现象。
4. 若重试后仍反复失败，需获取 BuildKit daemon 日志（`journalctl -u buildkit` 或容器日志）以确认 `graceful_stop` 的具体原因（OOM Kill / 超时信号 / 外部终止）。
