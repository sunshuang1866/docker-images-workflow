# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像源下载失败
- 新模式症状关键词: Curl error, HTTP/2 framing, INTERNAL_ERROR, No more mirrors to try, Error downloading packages

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`:4（`RUN yum install ...` 步骤）
- 失败原因: 在 aarch64 构建节点上，从 `repo.openeuler.org` 下载 `openEuler-24.03-LTS-SP4` 仓库的软件包时，多个包（gcc、kernel-headers、perl-MIME-Base64、vim-common）遭遇 HTTP/2 流错误和 SSL 连接中断，最终 `vim-common` 耗尽所有镜像源重试后仍无法下载，导致 `yum install` 失败退出码 1。

### 与 PR 变更的关联
**与 PR 改动无关。** 该 PR 仅新增了一个标准的 Dockerfile（安装常见开发依赖、克隆源码、cmake 编译），`yum install` 命令本身语法正确、包名有效（日志中 Dependencies resolved, Transaction Summary 等阶段均正常完成，表明仓库元数据已成功加载且包依赖解析通过）。失败纯粹发生在包下载传输阶段，属于 `repo.openeuler.org` 远端仓库的瞬时网络 / HTTP/2 服务端故障。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 openEuler 官方 yum 源（`repo.openeuler.org`）在特定时段对 aarch64 架构包的 HTTP/2 服务不稳定导致的临时性基础设施故障。处理方式：
- 在 Jenkins 上重新触发 aarch64 构建 job，等待镜像源恢复后重试即可。
- 若该问题频繁复现，可考虑在 CI 流水线中为 `yum install` 步骤增加自动重试机制（如 `yum install ... || (sleep 30 && yum install ...)` 或使用 `--retries` 相关参数），以应对短暂网络抖动。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在失败时间段（2026-07-09 13:44-14:08 UTC）是否存在 aarch64 仓库服务端异常或网络故障。
- 确认 CI 环境中是否可配置额外的镜像源（mirror）以提供冗余。

## 修复验证要求
（无需填写，本失败为 infra-error，不涉及代码修复）
