# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 被终止
- 新模式症状关键词: graceful_stop, no builder found, closing transport, rpc error, Unavailable

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 #7（`dnf install` 系统包安装阶段）
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在实际构建启动仅约 39 秒后被外部终止（收到 `graceful_stop` 的 gRPC GOAWAY 信号），随后构建客户端失去 builder 连接，构建中断。

### 与 PR 变更的关联
**无关**。PR 仅新增了一个 Dockerfile（为标准 `scann 1.4.2` 镜像添加 `24.03-lts-sp4` 变体）及配套的 README、image-info.yml、meta.yml 更新。构建在 DNF 安装基础系统包阶段即失败，远未到达运行 PR 特有任何自定义逻辑的阶段。该错误是 CI 基础设施侧的 BuildKit builder 资源被回收/超时/节点漂移导致的，与 PR 代码内容无因果关系。

## 修复方向

### 方向 1（置信度: 高）
**重试构建即可**。该失败属于 CI 基础设施的偶发性 builder 回收问题，无需修改任何 Dockerfile 或代码。在 CI 界面重新触发该 job 即可，多数情况下重试后能正常通过。

### 方向 2（置信度: 低）
若多次重试后仍在同一阶段（`dnf install` 下载 repo metadata）超时失败，可能是 `dlcdn.apache.org` 源或其他 openEuler 仓库在当前 builder 节点的网络连通性存在问题，可考虑临时换源处理。

## 需要进一步确认的点
- 检查该 CI job 是否有构建超时限制（日志中 `dnf install` 步骤从启动到 builder 被终止约 39 秒），若超时阈值设置过低也可能触发 builder 回收。
- 若该 builder 节点频繁出现 `graceful_stop`，建议排查 CI 集群的资源调度策略（如 builder 闲置时间阈值、节点抢占策略等）。
