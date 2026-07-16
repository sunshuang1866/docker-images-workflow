# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, Curl error (56), Failure when receiving data from the peer, yum install, No more mirrors to try, repo.openeuler.org

## 根因分析

### 直接错误

```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm [HTTP/2 stream 59 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: CI 在 aarch64 节点上执行 `yum install` 时，`repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 仓库镜像出现间歇性 HTTP/2 流错误（Stream error / INTERNAL_ERROR）和 SSL 读取失败，导致多个 RPM 包（gcc、kernel-headers、perl-MIME-Base64、vim-common）下载中断。其中 gcc、kernel-headers、perl-MIME-Base64 通过镜像重试成功，但 vim-common 耗尽所有可用镜像后仍失败，yum 安装整体退出码为 1。

### 与 PR 变更的关联
**与 PR 变更无关**。本次 PR 仅新增了一个标准格式的 brpc Dockerfile（`yum install` → `git clone` → `cmake && make`）及配套的 README.md、image-info.yml、meta.yml 元数据文件。Dockerfile 语法和构建逻辑正确，yum 包列表（git、gcc、gcc-c++、make、cmake、openssl-devel、gflags-devel、protobuf-devel、abseil-cpp-devel、leveldb-devel、snappy-devel）均为 openEuler 24.03-LTS-SP4 仓库合法存在的包。失败完全由仓库镜像的网络波动导致，非 PR 代码变更引起。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。本次失败为 openEuler 仓库镜像瞬时网络不稳定导致，`repo.openeuler.org` 的 HTTP/2 服务端在 CI 构建期间出现间歇性流中断。由于大多数包的镜像重试机制已自动恢复（gcc、kernel-headers 等），仅 vim-common 的重试次数耗尽，属于典型的瞬时网络故障。直接重新触发 CI 构建即可，概率很高能够成功。

### 方向 2（置信度: 中）
**增强 yum 重试韧性配置**。在 Dockerfile 的 `yum install` 命令中增加重试相关参数（如 `--setopt=retries=15` 或 `--setopt=timeout=120`），降低因仓库镜像瞬时波动导致的构建失败概率。但这不是 PR 代码的问题，属于 CI 基础设施层面的优化建议。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 的 aarch64 仓库镜像（`repo.openeuler.org`）在 CI 构建时段是否存在已知的 HTTP/2 服务端问题或负载异常。
- 如果相同 build node 上其他 PR 的构建也出现类似问题，则进一步确认属于 infra 侧问题；如果仅本次出现，可简单地重试构建。
