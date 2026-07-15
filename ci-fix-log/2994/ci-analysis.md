# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 被终止
- 新模式症状关键词: no builder found, closing transport, graceful_stop, goaway, euler_builder

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建阶段 Step 7/4（`RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`）
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在 dnf 下载 OS 仓库元数据过程中被外部信号终止（graceful_stop），导致构建连接断开，构建失败

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了一个标准 Dockerfile（安装系统包 → 编译 Python 3.9.19 → pip 安装 scann）以及配套的 README、image-info.yml、meta.yml 元数据更新。构建在执行第一个 `dnf install` 命令（Step 7/4）期间，BuildKit daemon 被外部调度器/控制器主动发送 GOAWAY 信号关停，属于 CI 基础设施层面的问题，并非 Dockerfile 内容或代码变更引起。

日志证据：
- Docker 构建在 Step 7（`dnf install`）下载元数据到 38.59s 时 BuildKit 连接断开
- `graceful_stop` + `code: NO_ERROR` 表明 builder 是被外部主动终止，而非自身崩溃
- 后续 `no builder "euler_builder_20260709_224657" found` 确认 builder 已被完全清理/移除

## 修复方向

### 方向 1（置信度: 高）
**无需修复代码**。这是 CI runner / BuildKit builder 被外部终止导致的基础设施故障，Code Fixer 无需处理。建议触发 CI 重试（re-run），若重试后仍失败需排查 CI runner 资源调度或 builder 超时配置。

## 需要进一步确认的点
1. `euler_builder_20260709_224657` 被 graceful_stop 的具体原因：是 CI 系统的 builder 存活时间限制（TTL 到期），还是 runner 节点资源压力触发驱逐，或是 `dnf` 下载速度过慢触发了超时保护
2. 同批次其他 PR 的构建是否也遭遇了 builder 被终止的情况（判断是否为系统性问题）
3. 若重试后仍失败，需获取 BuildKit daemon 日志确认终止来源
