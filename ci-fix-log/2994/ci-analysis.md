# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit builder 断连
- 新模式症状关键词: closing transport, connection error, EOF, goaway, graceful_stop, no builder found, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Dockerfile 第 9 行 `dnf install` 步骤（日志中标记为 `#7 [2/4]`）
- 失败原因: CI 构建环境的 BuildKit builder 实例 `euler_builder_20260709_224657` 在执行 `dnf install` 下载操作系统仓库元数据期间被优雅关闭（`graceful_stop` goaway），导致 gRPC 传输层连接断开（EOF），构建客户端无法与 builder 通信。这与 PR 代码变更无关，属于 CI 基础设施层面的偶发性故障。

### 与 PR 变更的关联
**无关。** PR 新增了一个全新的 Dockerfile（`Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`）以及配套的 README、meta.yml、image-info.yml 更新，所有变更均为标准的新镜像注册操作。故障发生在 `dnf install` 下载仓库元数据的网络 I/O 阶段，是 BuildKit builder 节点意外退出所致，Dockerfile 内容本身没有问题。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 这是一个典型的 CI 基础设施故障（BuildKit builder 节点崩溃/被回收），与代码无任何关联。Code Fixer 无需修改任何文件，只需重新触发 CI pipeline 即可。若连续多次重试均在同一阶段失败，则需排查 CI 构建节点的资源配额或 BuildKit daemon 稳定性。

## 需要进一步确认的点
- 若重试后仍然在 `dnf install` 步骤失败，需检查 `openeuler/openeuler:24.03-lts-sp4` 基础镜像的仓库配置是否正确、构建节点是否能正常访问 openEuler 官方 yum 源。
- 若重试后构建成功但在后续 check/test 阶段失败，需获取下游架构专属构建 job（如 aarch64）的日志进一步分析。
