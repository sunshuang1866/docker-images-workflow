# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler 仓库 HTTP/2 传输错误
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
#7 ERROR: process "/bin/sh -c yum install -y         git gcc gcc-c++ make cmake which ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: CI aarch64 构建节点在从 `repo.openeuler.org` 下载 173 个 RPM 包时，多次遭遇 HTTP/2 流错误（`INTERNAL_ERROR`）和 SSL 读取错误（`SSL_ERROR_SYSCALL`），导致 `gcc`、`kernel-headers`、`perl-MIME-Base64`、`vim-common` 等多个包下载失败。`vim-common`（7.8 MB，最后一个需要下载的包）重试全部镜像均失败后，yum 事务中止，构建退出码为 1。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 中 `yum install` 命令语法正确、包名存在且被 yum 成功解析（日志第 198.5 行正确列出了待安装的 173 个包清单）。失败纯粹由 CI 构建节点与 `repo.openeuler.org` 之间的网络传输层问题引起（HTTP/2 连接被远端非正常关闭、SSL 读取 syscall 错误），属于 CI 基础设施/上游镜像站网络故障。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 此为 `repo.openeuler.org` 镜像站的瞬时网络故障，Dockerfile 本身无需任何修改。等待镜像站恢复后重新触发 CI 构建即可通过。

### 方向 2（置信度: 低）
若 `repo.openeuler.org` 对 aarch64 架构的 HTTP/2 服务持续不稳定，可考虑在 Dockerfile 的 `yum install` 前增加重试逻辑（如 `yum install -y ... || yum install -y ...`），或通过 `yum.conf` 配置关闭 HTTP/2（`http2=0`）使用 HTTP/1.1 绕过。但这属于 workaround 而非根因修复，首选方案仍是方向 1。

## 需要进一步确认的点
- 检查 `repo.openeuler.org` 当时的服务状态，确认是否为上游镜像站临时故障。
- 确认同时间其他 openEuler 24.03-LTS-SP4 aarch64 构建是否也出现类似下载失败（若普遍存在则确认为上游问题）。
- 若重试后仍失败，需检查 CI aarch64 构建节点的网络防火墙/代理配置是否干扰了 HTTP/2 长连接。
