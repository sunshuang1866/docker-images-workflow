# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器异常终止
- 新模式症状关键词: graceful_stop, no builder found, closing transport, rpc error, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4] RUN dnf install ...` 执行期间
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 过程中被异常关闭（收到 `graceful_stop` 信号后连接断开），导致 BuildKit 客户端无法继续通信，构建中断。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个 Dockerfile（`Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`）和三项文档/元数据更新。构建在 `dnf install` 依赖包（`gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`）的元数据下载阶段即因 BuildKit 基础设施问题而中断，此时的构建步骤与 PR 中新增 Dockerfile 的特定内容（如 `RUN` 依赖清单）完全一致——是该 Dockerfile 的通用系统依赖安装环节，任何正常 Dockerfile 在此阶段都会执行类似操作。失败源于 CI 基础设施中 BuildKit builder 进程的异常终止，而非 PR 代码缺陷。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 该失败属于 CI 基础设施问题（BuildKit builder 实例意外终止），应重新触发 CI 运行（re-run job）。若持续出现同类错误，需排查 CI 构建节点的 BuildKit daemon 稳定性（是否存在内存/磁盘资源不足、OOM killer 或 builder 生命周期管理 bug）。

## 需要进一步确认的点
- BuildKit builder 实例 `euler_builder_20260709_224657` 被 `graceful_stop` 的具体原因（是否由资源不足、超时策略、或外部进程终止触发），需查看 CI 构建节点的系统日志（`dmesg`/`journalctl`）确认是否存在 OOM 或 builder 服务崩溃。
- 重试后是否复现：若重试后仍失败，需进一步检查是否 `dnf` 仓库连通性问题触发了 builder 连接超时。

## 修复验证要求
不适用（infra-error，无需代码修改，重试 CI 即可验证）。
