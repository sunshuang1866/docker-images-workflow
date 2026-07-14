# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 1709.7   guile-5:2.2.7-6.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: 在 aarch64 runner 上执行 `dnf install` 时，`repo.openeuler.org` 的多项 HTTP/2 传输流异常关闭（Curl error 92: INTERNAL_ERROR），其中 `git-core` 和 `gcc-c++` 在重试后成功下载，但 `guile` 包重试耗尽所有镜像后仍失败，导致 dnf 安装中断。

### 与 PR 变更的关联
**与 PR 改动无关**。PR 仅新增了 vvenc 的 Dockerfile 及配套元数据文件（README、image-info.yml、meta.yml），Dockerfile 内容为标准的 `dnf install` + `git clone` + `cmake` 构建流程，无任何错误配置。失败根因是 `repo.openeuler.org` 镜像站 aarch64 仓库在构建时段的 HTTP/2 传输层存在间歇性故障，导致部分 RPM 包下载失败。该问题对任何依赖 `dnf install` 从 openEuler 24.03-LTS-SP4 仓库下载包的 Dockerfile 均可能触发。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复**。这是 CI 基础设施/上游镜像站的临时网络问题。建议重试 CI 构建（re-run），等待 `repo.openeuler.org` 的 HTTP/2 服务恢复正常。如果多次重试均失败，可在 Dockerfile 中为 `dnf` 添加 `--setopt=timeout=300 --setopt=retries=10` 参数增加重试容忍度，但这不是根本解决方案。

### 方向 2（置信度: 低）
若镜像站 HTTP/2 问题持续存在，且 dnf 侧无法有效规避，可考虑在 Dockerfile 的 `dnf install` 前添加 `echo "http2=false" > /etc/dnf/dnf.conf.d/http2.conf`（或设置 `http2=false`），降级为 HTTP/1.1 绕过 HTTP/2 帧层错误。此方案为 workaround，可能影响下载速度。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` aarch64 仓库在构建时段（2026-07-09 14:09 UTC）是否存在已知的 HTTP/2 服务异常。
- 确认 `guile-2.2.7-6.oe2403sp4.aarch64.rpm` 文件是否确实存在于仓库中（排除文件缺失导致的 404 被误报为 HTTP/2 错误的可能性）。
- 可尝试在其他 runner（不同网络环境）重试相同构建，验证是否为特定 runner 到镜像站的网络链路问题。
