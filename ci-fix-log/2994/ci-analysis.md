# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 被终止
- 新模式症状关键词: `closing transport`, `graceful_stop`, `no builder`, `rpc error: code = Unavailable`, `error reading from server: EOF`

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4] RUN dnf install ...`（dnf 正在下载仓库元数据时）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在构建中途被外部信号终止（`graceful_stop` goaway 帧），导致 gRPC 传输连接关闭，构建进程被中断。该错误与 PR 代码变更无关，属于 CI 基础设施层面的构建器意外终止。

### 与 PR 变更的关联
无关。PR 仅新增了一个标准的 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 及配套元数据文件（README、image-info.yml、meta.yml）。Dockerfile 中触发构建中断的 `dnf install` 命令安装的是常规编译工具（gcc、gcc-c++、make、wget、openssl-devel 等），不存在语法错误或不符合规范的配置。构建失败的原因是 BuildKit daemon 在 `dnf` 执行期间被外部终止，与 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题，无需修改任何代码。重新触发 CI 构建即可。若持续复现，需由 CI 运维团队排查 BuildKit builder 实例为何在构建中途被终止（可能原因：runner 资源不足触发 OOM、构建超时被 CI 编排层 kill、runner 节点主动下线等）。

## 需要进一步确认的点
- Builder `euler_builder_20260709_224657` 被终止的具体原因（OOM、超时、节点回收等），需查看 runner 节点的系统日志或 CI 编排平台的后台记录。
- 若重新触发后仍以相同方式失败，需确认该 runner 节点是否存在稳定性问题或资源配额限制。
