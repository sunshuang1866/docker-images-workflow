# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: Docker构建器断连
- 新模式症状关键词: `graceful_stop`, `no builder found`, `closing transport due to: connection error`, `error reading from server: EOF`

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Dockerfile 的 `RUN dnf install` 步骤（Dockerfile 第 9 行，构建步骤 [2/4]）
- 失败原因: Docker BuildKit 构建器实例（`euler_builder_20260709_224657`）在 `dnf` 下载元数据阶段被异常终止。BuildKit 返回的 `graceful_stop` 表明构建器被外部信号关闭，构建进程随之中断。dnf 元数据下载速度仅 77 kB/s，下载 2.8 MB 耗时 37+ 秒，网络较慢可能是触发超时或节点调度的诱因，但本质上属于 CI 基础设施层面的问题。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增 scann 1.4.2 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件。构建失败发生在 `dnf install` 系统基础包（gcc、gcc-c++、make、wget、openssl-devel 等）的元数据下载阶段，尚未执行到 PR 新增的 Python 编译或 pip 安装步骤。这些系统包是 openEuler 官方仓库中的标准包，不存在缺失或版本问题。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 该失败为临时性基础设施问题（构建器节点被回收或连接中断），与代码无关。直接重新运行 CI pipeline 即可，大概率通过。

### 方向 2（置信度: 低）
如果重试后仍反复出现同一错误，可能是 CI 构建节点的 Docker BuildKit 或网络配置存在问题，需联系 CI 运维团队排查构建节点健康状态。

## 需要进一步确认的点
- 若重试后仍失败，需确认 CI 构建节点的 BuildKit 日志（daemon 日志、节点资源使用情况）以排除节点故障。
- `graceful_stop` 的具体触发原因：是节点资源不足（OOM）、构建超时策略触发、还是节点被外部调度系统回收。

## 修复验证要求
无需验证（infra-error，与代码无关）。
