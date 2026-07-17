# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2传输错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing, Stream error, Curl error (56), SSL_ERROR_SYSCALL, INTERNAL_ERROR, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`RUN yum install ...` 步骤）
- 失败原因: CI aarch64 runner（`ecs-build-docker-aarch64-04-sp`）在从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 的 173 个依赖 RPM 包时，先后遇到 4 次 HTTP/2 传输层错误（Curl error 92/56），其中 `vim-common` 包的所有镜像重试均失败，导致 `yum install` 以 exit code 1 退出，Docker 构建中断。

### 与 PR 变更的关联

**与 PR 改动无关。** PR 新增了一个语法正确、依赖声明合理的 Dockerfile（安装 gcc、cmake、protobuf-devel 等标准编译工具链）。172 个包成功下载，仅 4 个包因网络传输问题出现间歇性失败，最终仅 `vim-common` 成为压倒构建的最后一个失败。错误全部发生在 yum 通过网络从 `repo.openeuler.org` 下载 RPM 的阶段，与 Dockerfile 中声明的包名、版本、或任何构建逻辑无关。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试。** 该失败为 aarch64 CI runner 与 `repo.openeuler.org` 之间的 HTTP/2 传输层网络波动（`INTERNAL_ERROR` / `SSL_ERROR_SYSCALL`）导致。这是典型的间歇性基础设施问题，非代码缺陷。在 CI 侧重新触发该 job 有较大概率直接通过（173 个包大部分已成功下载，仅少数大包如 `vim-common` 7.8MB 在传输中途被 reset）。

### 方向 2（置信度: 低）
若重试持续失败，可在 Jenkins pipeline 中的 Docker build 之前增加 `yum makecache` 并设置 `retries=5` 的 yum 配置，或考虑在 Dockerfile 中为 `yum install` 命令添加 `--setopt=retries=10` 参数以提高网络波动容忍度。但这属于 CI 基础设施层面的改进，不应由本 PR 承担。

## 需要进一步确认的点

- 确认 `repo.openeuler.org` 在故障时段是否有已知的 CDN/镜像站服务降级事件。
- 确认 `ecs-build-docker-aarch64-04-sp` runner 节点的出网链路在故障时段是否稳定。
- 若重试 2-3 次后仍持续失败，需排查该 runner 到 `repo.openeuler.org` 的网络路由及 DNS 解析是否异常。
