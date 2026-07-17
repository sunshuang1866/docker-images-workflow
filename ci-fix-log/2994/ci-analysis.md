# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 被终止
- 新模式症状关键词: graceful_stop, no builder found, rpc error, closing transport, EOF, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`（dnf install 执行中，约 38 秒处）
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在构建过程中被触发 `graceful_stop`（优雅关闭），导致已建立的 RPC 连接被中断，客户端收到 `EOF` 后报错。构建随后因找不到 builder 而失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了一个 Dockerfile 和对应的元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 内容为标准的 dnf 安装、源码编译 Python、pip 安装 scann，无语法错误或逻辑问题。构建在 `dnf install` 阶段（尚未执行到 PR 特有的 Python 编译或 pip 安装步骤）因 BuildKit 基础设施异常而中断，非本次改动触发。

## 修复方向

### 方向 1（置信度: 中）
**重新触发 CI**。BuildKit builder 的 `graceful_stop` 通常由 CI 编排层触发（如节点维护、资源回收、超时清理），属于临时性基础设施问题，与代码质量无关。重新执行 CI pipeline 大概率可以成功构建。

### 方向 2（置信度: 低）
如重试后持续失败，需排查 CI 基础设施侧：检查构建节点 `ecs-build-docker-x86-hk` 的资源状态、builder 生命周期管理策略，以及是否存在 builder 超时时间过短导致正常构建被误杀的情况。

## 需要进一步确认的点
- 确认 `euler_builder_20260709_224657` 被 graceful_stop 的原因（节点维护 / 资源不足 / 超时 / 其他 builder 生命周期策略），此信息不在当前日志中，需查看 BuildKit builder 的调度/管理日志。
- 如重试 CI 后仍然失败，需对比同批次其他成功构建的镜像，确认是否仅有该 builder 异常。
