# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 崩溃
- 新模式症状关键词: no builder found, BuildKit, graceful_stop, closing transport, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 #7（`dnf install` 安装 gcc/gcc-c++/make/wget/openssl-devel/bzip2-devel/zlib-devel）
- 失败原因: Docker BuildKit builder 实例 `euler_builder_20260709_224657` 在执行 `dnf install` 下载 OS 元数据过程中（耗时约 38.6 秒，下载 2.8 MB）被优雅关闭（`graceful_stop`），导致 gRPC 传输层连接中断，构建无法继续。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 和三条元数据记录（README.md、image-info.yml、meta.yml），均为纯文本追加操作，不涉及任何可能影响 BuildKit builder 行为的配置。Docker 构建在基础镜像层之后、系统包安装阶段因 builder 实例销亡而失败，属于 CI 基础设施偶发故障。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 此为 CI 基础设施的 BuildKit builder 实例崩溃/被回收导致的偶发失败。应重新触发 CI 构建即可。若反复出现，需由 CI 运维团队排查 BuildKit builder 的稳定性（是否存在资源不足、超时回收、或节点故障等问题）。

## 需要进一步确认的点
- 确认 `euler_builder_20260709_224657` 被 `graceful_stop` 的原因（是否为 CI 调度器主动回收、节点 OOM、或健康检查失败）。
- 如果重新触发 CI 多次后依然在同一阶段失败，需排查 `dnf install` 下载 OS 元数据期间是否存在网络波动触发 builder 超时回收。

## 修复验证要求
（无需填写——本次失败为 infra-error，不涉及代码修复。）
