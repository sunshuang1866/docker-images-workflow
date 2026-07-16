# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: "BuildKit 构建器意外终止"
- 新模式症状关键词: graceful_stop, no builder found, closing transport, error reading from server: EOF

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`（`dnf install` 下载仓库元数据阶段）
- 失败原因: BuildKit 构建器（`euler_builder_20260709_224657`）在 `dnf install` 执行过程中被意外终止。构建器 daemon 发送了 GOAWAY 帧（`code: NO_ERROR, debug data: "graceful_stop"`）后关闭连接，导致 Docker 构建客户端无法继续通信。构建失败后构建器已被清理（`no builder found`）。

### 与 PR 变更的关联
**与 PR 变更无关。** 构建失败发生在 `dnf install` 基础系统包安装阶段，该阶段远在 PR 中新增的任何自定义步骤（Python 3.9 编译安装、scann pip 安装）之前。构建失败是 CI 基础设施层面的 BuildKit 容器意外终止导致的，与 Dockerfile 内容无直接因果关系。PR 变更仅涉及新增 openEuler 24.03-LTS-SP4 的 Dockerfile、README.md 更新、meta.yml 和 image-info.yml 元数据补充，均为常规文件，不包含可能引发构建器崩溃的特殊指令。

## 修复方向

### 方向 1（置信度: 中）
触发 CI 重试（re-run）。该失败为 BuildKit 构建器 daemon 在构建过程中被意外终止的瞬态基础设施故障，非代码/配置问题。常见的触发原因包括 CI runner 资源耗尽（OOM）、构建器容器超时被清理、或宿主机节点维护重启。通常重试即可通过。

### 方向 2（置信度: 低）
若多次重试均在同一位置失败（`dnf install` 下载仓库元数据阶段），则可能是 `openeuler:24.03-lts-sp4` 基础镜像的 `dnf` 仓库配置在与 BuildKit `docker-container` 驱动的兼容性上存在问题。此时需要进一步调查 `openeuler:24.03-lts-sp4` 镜像的 `/etc/yum.repos.d/` 仓库数量与 BuildKit 容器网络初始化时序的互动。

## 需要进一步确认的点
1. 该 x86-64 构建 job 是否多次重试均以相同错误失败？若首次失败且重试后通过，确认是瞬态 infra 故障。
2. 对应的 aarch64 构建 job（若有）是否也失败？若 aarch64 通过而 x86-64 反复失败，需排查 x86-64 runner 节点的 BuildKit 配置或资源状态。
3. 本次构建使用的 `euler_builder_*` 命名模式是否意味着构建器实例有生命周期管理问题（如创建后立即被回收）。
