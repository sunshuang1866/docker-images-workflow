# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: YUM仓库下载网络波动
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org, yum install

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
#7 ERROR: process "/bin/sh -c yum install -y         git gcc gcc-c++ make cmake which         openssl-devel         gflags-devel         protobuf-devel protobuf-compiler         abseil-cpp-devel         leveldb-devel snappy-devel &&     yum clean all && rm -rf /var/cache/yum" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Dockerfile:4`（`RUN yum install -y ...` 步骤，aarch64 架构）
- 失败原因: CI 构建节点从 `repo.openeuler.org` 下载 RPM 包时遭遇 HTTP/2 流错误（Curl error 92）和 SSL 读取失败（Curl error 56），共 4 个包（gcc、kernel-headers、perl-MIME-Base64、vim-common）出现下载异常。前 3 个在 yum 自动重试后成功下载，但 `vim-common` 在耗尽所有镜像重试后仍下载失败，导致整个 yum install 步骤退出码为 1。

### 与 PR 变更的关联
**与 PR 代码变更无关**。PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 和配套元数据文件。Dockerfile 中 `yum install` 的命令语法正确，所有声明的包在仓库中均真实存在（yum 已成功解析依赖关系，列出 173 个待安装包）。`vim-common` 并非 Dockerfile 显式指定的包，而是作为传递依赖（被 git 的弱依赖链引入，路径为 `git → perl-Git → perl → vim-enhanced → vim-common`）。失败是上游镜像仓库 `repo.openeuler.org` 在该时段网络不稳定的瞬态问题。

## 修复方向

### 方向 1（置信度: 中）
**重新触发 CI 构建**。这是网络瞬态故障，`repo.openeuler.org` 在该时间窗口内 HTTP/2 连接不稳定。172/173 个包下载成功，仅有 1 个失败，且失败的都是大文件包（gcc 30MB、kernel-headers 1.7MB、vim-common 7.8MB），呈现典型的网络波动特征。直接重试大概率可以成功，无需修改任何代码。

### 方向 2（置信度: 低）
如果多次重试后 `vim-common` 依然失败，可能是 `repo.openeuler.org` 上该特定架构的 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 文件本身损坏。此时需要在 Dockerfile 中绕过 vim 依赖链，例如安装 `git-core` 而非 `git`（避免引入 vim-enhanced），或在 yum install 中显式排除 vim 相关包：`yum install -y --setopt=install_weak_deps=False ...`。

## 需要进一步确认的点
1. `repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 文件是否在仓库中完整可用（非瞬态网络问题时可手动 wget 校验）。
2. 当前 CI 的 aarch64 构建节点 `ecs-build-docker-aarch64-04-sp` 到 `repo.openeuler.org` 的网络链路是否存在持续性问题。
3. 如果重试后仍然失败，需要确认是否需要在 Dockerfile 中显式添加 `vim-common` 到 install 列表中以触发提前下载，或通过 `--setopt=install_weak_deps=False` 减少传递依赖的安装量。
