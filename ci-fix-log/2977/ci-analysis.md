# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像网络波动
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, yum install, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install` 步骤）
- 失败原因: aarch64 构建节点在 `yum install` 下载 173 个 RPM 包的过程中，`repo.openeuler.org` 仓库镜像出现多次 HTTP/2 传输层错误（Curl error 92: INTERNAL_ERROR），gcc、kernel-headers、perl-MIME-Base64 三个大包均触发重试后成功，但最后一个包 `vim-common`（7.8 MB，第 173/173 个）重试也失败，导致整个 yum 事务失败退出。

### 与 PR 变更的关联
**与 PR 无关**。PR 仅新增了一个 Dockerfile 及元数据文件，为 openEuler 24.03-LTS-SP4 添加 brpc 1.16.0 的镜像支持。Dockerfile 中 `yum install` 的命令语法、包名均正确，失败纯粹是由于 aarch64 构建节点访问 `repo.openeuler.org` 仓库时遭遇了网络层面的 HTTP/2 流传输异常。

同期日志中同一构建过程出现 4 次独立的 Curl 网络错误（gcc、kernel-headers、perl-MIME-Base64、vim-common），其中前 3 次均通过 dnf/yum 的重试机制恢复，唯独 vim-common 的重试也耗尽。这进一步说明是仓库服务端或中间网络链路的瞬时不稳定，而非 Dockerfile 配置问题。

## 修复方向

### 方向 1（置信度: 中）
**触发 CI 重试**。这是典型的 infra-error（仓库网络波动），Dockerfile 本身无需修改。重新触发一次 CI 构建大概率会通过——同批次构建中 gcc、kernel-headers 等同仓库的大文件重试后均下载成功，vim-common 只是运气最差的那个。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 CI 失败时间段是否有服务端侧的网络抖动或 CDN 节点异常。
- 确认 aarch64 构建节点（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络链路是否稳定。
- 如果多次重试均在同一包（vim-common）上失败，则需检查该 RPM 文件在 openEuler 24.03-LTS-SP4 仓库镜像中是否完整可用。
