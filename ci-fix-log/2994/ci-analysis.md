# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: 构建器异常终止
- 新模式症状关键词: gracefult_stop, no builder found, rpc error, connection error: EOF

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`，`dnf install` 正在下载仓库元数据时
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在构建中途被服务端主动关闭（goaway 信号 `graceful_stop`），导致构建连接断开，构建器实例随后被清理

### 与 PR 变更的关联
与 PR 代码变更**无关**。失败发生在 Docker 构建基础设施层面（BuildKit builder 异常终止），而非 Dockerfile 内容或构建逻辑问题。PR 仅新增了一个 Dockerfile 和配套元数据文件，构建在 `dnf install` 步骤中因构建器被关闭而中断，未能执行到后续步骤（Python 编译、scann pip 安装）。从日志中 `dnf install` 正在正常下载元数据（77 kB/s）来看，该步骤本身无报错，是外部因素导致构建中断。

## 修复方向

### 方向 1（置信度: 低）
CI 基础设施问题，Code Fixer **无需处理**。此失败是 BuildKit 构建器节点异常关闭导致，可能原因包括：
- Runner 节点资源耗尽（OOM、磁盘满）被调度器驱逐
- Runner 节点进入维护模式（drain）主动回收
- CI Job 超时（`dnf install` 下载元数据速度仅 77 kB/s，远低于正常水平，可能导致整体超时）

建议：重新触发 CI 构建。若反复出现相同错误，需要 CI 运维团队排查 runner 节点的资源状况或网络连通性。

## 需要进一步确认的点
1. 由于构建在步骤 2/4 即被中断，无法验证后续步骤（Python 3.9.19 源码编译、scann pip 安装）是否能正常通过。需要一次成功的 CI 运行来完整验证 Dockerfile。
2. `dnf install` 元数据下载速度仅 77 kB/s，显著偏慢，需确认 CI runner 到 openEuler 仓库的网络质量是否正常。
3. 对比同类 scann 24.03-lts-sp3 的 Dockerfile，确认依赖包列表是否一致。

## 修复验证要求
不适用 — 失败类型为 infra-error，无需代码修复。
