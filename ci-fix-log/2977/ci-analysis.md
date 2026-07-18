# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像网络波动
- 新模式症状关键词: Curl error (92), Curl error (56), HTTP/2, INTERNAL_ERROR, SSL_ERROR_SYSCALL, repo.openeuler.org, MIRROR, No more mirrors to try, Error downloading packages

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
- 失败位置: Dockerfile:4（`RUN yum install -y ...` 步骤）
- 失败原因: aarch64 构建节点在从 `repo.openeuler.org` 下载 yum 软件包时，多次遭遇 HTTP/2 流异常关闭（Curl error 92）和 SSL 系统调用错误（Curl error 56），部分重试成功（如 `gcc` 和 `kernel-headers` 在重试后下载成功），但 `vim-common` 包在所有镜像源重试均失败后导致整个 `yum install` 步骤以退出码 1 失败。

### 与 PR 变更的关联
此失败与 PR 变更**无直接关联**。PR 仅新增了 `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`、更新 README、image-info.yml 和 meta.yml，属于常规的镜像版本新增操作。Dockerfile 中 `yum install` 的依赖列表与同项目下其他 openeuler:24.03-lts-sp4 的 Dockerfile 写法一致，不存在语法或参数错误。

失败的根本原因是 `repo.openeuler.org` 仓库服务器在构建时间段的 HTTP/2 传输不稳定，导致 173 个依赖包的并发下载中出现多次网络层面的 Curl 错误（在 aarch64 runner `ecs-build-docker-aarch64-04-sp` 上）。日志显示部分包经过重试后成功下载（`gcc` 在 556s 报错，831s 重试成功），但 `vim-common` 最终耗尽所有镜像重试机会而失败。

## 修复方向

### 方向 1（置信度: 高）
**重试触发 CI**：此失败为临时性网络/仓库服务端问题，与代码无关。等待 openEuler 镜像站 HTTP/2 服务恢复稳定后重新触发 CI 构建即可通过。无需对 Dockerfile 或任何代码文件做修改。

### 方向 2（置信度: 低）
**调整 yum 下载并发或禁用 HTTP/2**：如果该问题在 aarch64 架构上反复出现，可在 Dockerfile 中通过添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 或设置 curl 参数禁用 HTTP/2，降低并发下载时流异常的触发概率。但此方向属于绕过手段，非根本修复，且可能影响下载速度。

## 需要进一步确认的点
1. 该仓库镜像 `repo.openeuler.org` 在构建时段是否存在已知的 HTTP/2 服务异常或 CDN 故障。
2. 同一时间段内其他 PR 的 aarch64 构建是否也遭遇相同错误（若普遍出现，则可确认为基础设施问题）。
3. x86-64 架构的构建是否同样失败（日志仅提供了 aarch64 runner 的日志）。

## 修复验证要求
无需验证，建议直接重试 CI。若 `repo.openeuler.org` 的 HTTP/2 问题持续，可考虑联系 openEuler 基础设施团队排查 CDN 或镜像服务器配置。
