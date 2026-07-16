# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

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
- 失败位置: `Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: aarch64 CI runner 从 `repo.openeuler.org` 镜像站下载 RPM 包时，多次遇到 HTTP/2 协议层流错误（Curl error 92: INTERNAL_ERROR）和 SSL 连接中断（Curl error 56: SSL_ERROR_SYSCALL），最终 `vim-common` 包所有 mirrors 均尝试失败，yum 安装阶段退出码 1。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（共 25 行，标准的 `yum install` + `cmake && make` 构建流程）及配套文档/元数据文件。失败发生在 yum 从远端仓库下载 RPM 包阶段，Dockerfile 中列出的所有包名都是正确且有效的（gcc、gcc-c++、cmake 等 123 个包已成功下载，仅 vim-common 在最后由于镜像站 HTTP/2 传输异常而失败）。

日志中 gcc、kernel-headers、perl-MIME-Base64 也分别触发了 Curl error 92/56，但 yum 的重试机制使这些包后续下载成功；vim-common 是第 173/173 个要下载的包，其重试耗尽后整个事务失败。

## 修复方向

### 方向 1（置信度: 中）
**触发 CI 重跑**：该失败是 `repo.openeuler.org` aarch64 镜像站的瞬时网络/协议层问题，与 PR 代码无关。直接触发 Jenkins job 重跑（re-run），大概率能成功通过。

### 方向 2（置信度: 低）
若重跑持续失败，说明 repo.openeuler.org 对 aarch64 镜像站点的 HTTP/2 长时间不稳定，可考虑在 Dockerfile 中 yum install 前添加 retry 逻辑（如 `yum install --setopt=retries=10 ...`）为 yum 增加更长的重试窗口。但此方向不推荐，根因在镜像站而非 Dockerfile。

## 需要进一步确认的点
- 重跑 CI 后是否仍失败：若仍失败，需要检查 `repo.openeuler.org` 本体是否正常，以及该 aarch64 CI runner 与镜像站之间的网络链路是否稳定。
- 日志中仅显示了 aarch64 架构的构建失败；需确认 x86_64 构建是否也遇到类似问题。
