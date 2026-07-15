# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器断连
- 新模式症状关键词: rpc error, Unavailable, closing transport, connection error, error reading from server: EOF, graceful_stop, no builder found

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4] RUN dnf install`（`Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 的 dnf 安装步骤）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 过程中异常断开连接（gRPC 报 `Unavailable` + `graceful_stop`），构建器容器可能因 runner 资源耗尽、超时或被外部终止而消失，导致构建中断

### 与 PR 变更的关联
PR 变更仅为新增 scann 1.4.2 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套元数据/文档更新，Dockerfile 本身语法正确，`dnf install` 中列出的包（gcc、gcc-c++、make、wget、openssl-devel、bzip2-devel、zlib-devel）均为 openEuler 仓库中的标准包。构建在 dnf 下载 metadata 阶段（尚未开始安装具体包）时 builder 断连，**此失败与 PR 代码变更无关**，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 中）
此为 CI 基础设施故障（BuildKit builder 断连），Code Fixer 无需对 Dockerfile 做任何修改。建议直接重新触发 CI 构建（re-run），若多次重试仍失败，则需排查 CI runner 的资源配额（内存/磁盘）或 BuildKit builder 容器的稳定性。

## 需要进一步确认的点
- 同一 CI runner（`ecs-build-docker-x86-hk`）在相近时间段是否有其他构建也遇到 BuildKit builder 断连问题，以排除单点基础设施故障
- BuildKit builder 容器 `euler_builder_20260709_224657` 是否因 OOM（内存不足）被 kill，可在 runner 上检查 dmesg/syslog 中的 OOM killer 记录
- runner 的磁盘空间是否充足，`docker system df` 是否存在大量未清理的构建缓存导致空间耗尽
