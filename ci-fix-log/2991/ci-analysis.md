# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Stream error, INTERNAL_ERROR (err 2), repo.openeuler.org

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: CI 构建环境（aarch64 runner `ecs-build-docker-aarch64-04-sp`）在执行 `dnf install` 从 `repo.openeuler.org` 下载 RPM 包时，多个包（git-core、gcc-c++、guile）遭遇 HTTP/2 流错误（`Curl error (92): Stream error in the HTTP/2 framing layer`）。`guile` 包耗尽所有镜像重试后下载失败，导致 `dnf install` 以 exit code 1 退出。**此为 CI 基础设施层面的网络问题，与 PR 代码变更无关。**

### 与 PR 变更的关联
PR 仅新增了一个标准格式的 Dockerfile（`Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`），其 `dnf install` 命令与同类 Dockerfile（如已有的 `24.03-lts-sp3` 版本）完全相同，仅基础镜像版本由 `sp3` 变为 `sp4`。本次失败完全由 CI runner 与 openEuler RPM 仓库之间的网络连接不稳定导致，**PR 变更本身没有问题**。

## 修复方向

### 方向 1（置信度: 高）
**重试构建**。此失败由 repo.openeuler.org 的 HTTP/2 CDN 节点临时性问题导致（多个包的 HTTP/2 stream 被服务端异常关闭）。等待网络恢复后重新触发 CI 构建即可通过。

### 方向 2（置信度: 低）
若重试多次仍然失败，可考虑在 Dockerfile 中为 `dnf` 命令增加重试和超时参数，例如 `dnf install -y --setopt=retries=10 --setopt=timeout=30 ...`，或临时在 `dnf install` 前禁用 HTTP/2 以回退到 HTTP/1.1（`echo "http2=false" >> /etc/dnf/dnf.conf`）。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 CDN 节点在 aarch64 runner 所在网络区域是否已恢复正常。可在 CI runner 上手动执行 `curl -I https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/` 验证连通性。
- 确认同类 Dockerfile（如 `Others/vvenc/1.14.0/24.03-lts-sp3/Dockerfile`）在同一 CI 环境下是否能正常通过，以排除 repo 本身的问题。
