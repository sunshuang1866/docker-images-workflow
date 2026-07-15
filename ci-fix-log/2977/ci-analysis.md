# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库下载失败
- 新模式症状关键词: Curl error (92), Stream error in HTTP/2 framing layer, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

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
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上构建时，`yum install` 从 `repo.openeuler.org` 下载 173 个 RPM 包的过程中遭遇多次 HTTP/2 流错误（curl error 92）和 SSL 连接中断（curl error 56）。尽管前 3 个失败包（gcc、kernel-headers、perl-MIME-Base64）在 yum 自动重试后恢复，但 `vim-common-9.0.2092-36.oe2403sp4.aarch64` 下载重试耗尽所有镜像后最终失败，导致整个 `yum install` 命令退出码为 1。

### 与 PR 变更的关联
PR 变更仅新增了 `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`（标准 Dockerfile，yum install 依赖包列表与其他 SP3 同类文件一致），并更新了 README.md、image-info.yml、meta.yml 元数据文件。失败发生在 `yum install` 从 `repo.openeuler.org` 下载 RPM 包时的网络传输阶段，与 PR 的代码变更无关——Dockerfile 中指定的所有包名在目标仓库中均存在（yum 成功解析了依赖并识别出 173 个包），且日志中有大量 HTTP/2 流错误和 SSL 连接中断，属于 CI 构建节点到 openEuler 镜像仓库之间的网络基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
这是 CI 构建节点与 `repo.openeuler.org` 之间的网络基础设施问题。无需修改 PR 代码。正确的处理方式是 **重新触发 CI 构建**（retry），因为前 3 个遇到网络错误的包均在重试后下载成功，`vim-common` 的失败大概率也是同一类型的瞬时网络波动。如果多次重试后仍反复失败，需排查 CI runner 所在网段到 `repo.openeuler.org` 的网络链路质量或仓库端 HTTP/2 服务稳定性。

## 需要进一步确认的点
（无——日志证据充分，错误类型明确为网络基础设施问题，与 PR 代码无关。）

## 修复验证要求
（不适用——此类 infra-error 无需 code-fixer 介入。）
