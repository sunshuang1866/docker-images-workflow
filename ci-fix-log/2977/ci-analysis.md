# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, yum install

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`:4（`RUN yum install -y ...` 步骤）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上构建 Docker 镜像时，`yum install` 从 `repo.openeuler.org` 下载 RPM 包过程中多次遭遇 HTTP/2 流错误（Curl error 92）和 SSL 读错误（Curl error 56）。虽然多数包通过重试最终下载成功，但 `vim-common` 包的重试耗尽所有镜像源后最终失败，导致整个 `yum install` 步骤以 exit code 1 终止。

### 与 PR 变更的关联
**无关**。PR 仅新增了一个标准的 Dockerfile（安装编译依赖 → clone 源码 → cmake + make）、更新了 README.md、image-info.yml 和 meta.yml 的条目，Dockerfile 语法正确、依赖包名称有效。失败是由于 openEuler 官方软件仓库 `repo.openeuler.org` 在该次 CI 运行期间出现 HTTP/2 协议层面的间歇性连接问题，属于 CI 基础设施/上游服务故障。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。这是典型的上游仓库临时的网络故障（HTTP/2 stream INTERNAL_ERROR），与 PR 代码无关。等待 openEuler 软件仓库恢复后重新触发 CI 构建即可。若同一 PR 连续多次触发后仍然失败，可考虑在 Dockerfile 的 `yum install` 前增加 `yum makecache` 并设置 `--retries` 更高的值，或在 yum 配置中回退到 HTTP/1.1 以规避 HTTP/2 协议层面的问题。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在该时段是否有已知的服务中断或维护公告。
- 检查 CI 其他同时段运行的 aarch64 job 是否也有类似的 yum 下载失败（判断是单次偶发还是仓库侧持续故障）。
- 若重试后仍失败，需确认 `vim-common-9.0.2092-36.oe2403sp4.aarch64` 该 RPM 包在 openEuler 24.03-LTS-SP4 仓库中是否确实存在且可正常访问。
