# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器被终止
- 新模式症状关键词: graceful_stop, closing transport, no builder found, rpc error: code = Unavailable

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker build 第 2/4 步（`dnf install` 下载 OS 仓库元数据阶段）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在构建过程中被基础设施层主动优雅关闭（`graceful_stop`，GOAWAY 帧携带 `NO_ERROR` 状态码），导致与构建器的 RPC 连接断开。构建尚未进入 scann pip install 等实质性步骤。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准结构的 Dockerfile（安装编译工具链 → 编译 Python 3.9 → pip 安装 scann），以及配套的 README、image-info.yml、meta.yml 条目。构建在第一步 `dnf install` 下载仓库元数据时即因基础设施问题中断，尚未执行到任何与 PR 代码逻辑相关的步骤。所有新增文件无语法或格式问题。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 该失败是 BuildKit 构建器实例被基础设施层主动关闭所致（GOAWAY `graceful_stop` + `NO_ERROR`），属于临时性基础设施事件。无需修改任何代码，直接 retrigger CI 即可。若多次 retrigger 均在同一 dnf 步骤出现相同错误，则需检查 CI 构建节点的资源配额/超时策略或网络稳定性。

## 需要进一步确认的点
- 若 retrigger 后仍然失败，需确认 CI 构建节点是否存在时间配额限制（构建在 dnf 下载阶段耗时约 38 秒后被终止）
- 确认 `ecs-build-docker-x86-hk` 节点在对应时段的资源状态和调度事件
- 确认是否存在构建超时策略导致 BuildKit 实例被强制回收
