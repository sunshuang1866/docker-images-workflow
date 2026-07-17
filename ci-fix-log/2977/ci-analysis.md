# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站网络波动
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, repo.openeuler.org, yum install, No more mirrors to try

## 根因分析

### 直接错误
```
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y         git gcc gcc-c++ make cmake which         openssl-devel         gflags-devel         protobuf-devel protobuf-compiler         abseil-cpp-devel         leveldb-devel snappy-devel &&     yum clean all && rm -rf /var/cache/yum" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`RUN yum install` 步骤）
- 失败原因: CI 构建在 aarch64 节点上执行 `yum install` 时，`repo.openeuler.org` 镜像站出现 HTTP/2 连接层网络波动，多个 RPM 包下载过程中遭遇 Curl error (92)（HTTP/2 stream 未干净关闭）和 Curl error (56)（SSL 读取时对端断开）。虽然 gcc、kernel-headers、perl-MIME-Base64 等包通过重试成功下载，但 `vim-common` 包（最后一个待下载包）在上游超时/连接异常耗尽所有重试后彻底失败，导致整个 `yum install` 命令退出。
- 构建节点: `ecs-build-docker-aarch64-04-sp (docker-build-aarch64)`，aarch64 架构。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增以下文件：
- `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`（新 Dockerfile，用于构建 brpc 1.16.0 镜像）
- `Others/brpc/README.md`、`Others/brpc/doc/image-info.yml`、`Others/brpc/meta.yml`（文档/元数据更新）

失败发生在 `yum install` 从 `repo.openeuler.org` 下载 RPM 包的过程中，属于 openEuler 官方镜像站的网络基础设施问题，与 PR 的 Dockerfile 内容、依赖声明、CMake 配置等均无关联。其他已存在的同类型镜像（如 `24.03-lts-sp3`）在同样的构建环境下，若镜像站网络波动也会遇到相同故障。

## 修复方向

### 方向 1（置信度: 高）
**不属于代码层面可修复的问题。** 这是 `repo.openeuler.org` 镜像站的临时网络波动，属于 CI 基础设施故障。建议的操作：
- 等待镜像站网络恢复后**重试 CI**（jenkins rebuild）。
- 如果在短时间内反复出现相同问题，可在 Dockerfile 的 `yum install` 步骤前添加 `yum makecache && yum update -y` 或为 yum 配置增加 `retries` 和 `timeout` 参数，但这治标不治本，核心问题仍在于上游镜像站的稳定性。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 镜像站在故障时间点（2026-07-09 13:45 UTC 前后）是否存在网络波动或服务降级。
- 确认同一时间段内其他基于 openEuler 24.03-LTS-SP4 的 CI 构建任务是否也出现了类似的 yum 下载失败。
