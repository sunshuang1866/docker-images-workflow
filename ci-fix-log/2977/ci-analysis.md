# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM 镜像站下载中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, SSL_ERROR_SYSCALL, No more mirrors to try, yum install, repo.openeuler.org

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
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`yum install ...` 步骤）
- 失败原因: 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 `yum install` 从 `repo.openeuler.org` 下载 RPM 包时，多个包（gcc、kernel-headers、perl-MIME-Base64、vim-common）遭遇 HTTP/2 流错误（Curl error 92）和 SSL 连接中断（Curl error 56），最终 `vim-common` 因所有镜像源均尝试失败而下载失败，导致整个 yum install 返回 exit code 1。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准的 Dockerfile（安装依赖 → git clone → cmake → make → make install）以及配套的 README、image-info.yml、meta.yml 元数据文件。`yum install` 中的包列表（git、gcc、gcc-c++、make、cmake、openssl-devel 等）均为 openEuler 24.03-LTS-SP4 仓库中的标准包，没有任何语法错误或不存在的包名。失败根因是 `repo.openeuler.org` 镜像站在该时刻对 aarch64 构建节点的 HTTP/2 连接不稳定，属于临时性基础设施网络问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码**。该失败是 CI 基础设施的网络临时波动导致 `repo.openeuler.org` 镜像站 HTTP/2 流传输中断。Code Fixer 无需对 Dockerfile 或任何源码文件做任何修改。建议直接 re-run 失败的 CI job，在网络恢复后构建即可通过。若持续复现，考虑在 Dockerfile 的 yum install 命令中添加 `--retries 10` 或 `--setopt=retries=10` 提高 yum 下载重试次数以增加容错。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 镜像站在 aarch64 runner 所在网络环境中的连通性是否已恢复（可通过手动 curl/wget 测试包文件 URL）。
- 若 rerun 后仍反复失败，检查 CI runner 节点 `ecs-build-docker-aarch64-04-sp` 到 `repo.openeuler.org` 的网络路径是否存在持续性丢包或 HTTP/2 兼容性问题。
