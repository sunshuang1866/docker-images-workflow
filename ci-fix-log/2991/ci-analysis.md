# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler镜像站HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, dnf install

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: CI 的 aarch64 构建节点（`ecs-build-docker-aarch64-04-sp`）在通过 dnf 从 `repo.openeuler.org` 下载 RPM 包时，遇到 CDN 服务器 HTTP/2 流错误（Curl error 92），连续重试后 `guile` 包下载失败，导致整个 `dnf install` 命令返回 exit code 1。

### 与 PR 变更的关联
**与 PR 代码变更无关**。PR 新增的 Dockerfile（`Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`）语法正确，`dnf install` 命令中列出的包名（`git gcc gcc-c++ make cmake`）均为 openEuler 24.03-LTS-SP4 仓库中的有效包名，依赖解析阶段已经通过（Dependencies resolved，列出 156 个包待下载）。失败发生在后续的 RPM 包下载阶段，根因是 `repo.openeuler.org` CDN 服务器的 HTTP/2 实现存在间歇性问题，导致部分下载流被异常关闭。

## 修复方向

### 方向 1（置信度: 低）
**此问题无需 Code Fixer 处理**。该失败属于 CI 基础设施/上游镜像站的暂时性问题，不是 PR 代码缺陷。建议：
- 重新触发 CI 作业（retry），HTTP/2 流错误通常是间歇性的
- 如果持续复现，可以考虑在 Dockerfile 的 `dnf install` 前配置 dnf 禁用 HTTP/2（设置 `http2=False` 在 `/etc/dnf/dnf.conf` 中），强制使用 HTTP/1.1 下载 RPM 包

## 需要进一步确认的点
- 检查同一时间段内其他 PR 在 aarch64 节点上的构建是否也出现同样的 `Curl error (92)` HTTP/2 流错误，以确认是 `repo.openeuler.org` CDN 大面积故障还是单一节点网络问题
- 确认 `repo.openeuler.org` 的 HTTP/2 服务在 CI 运行时段（2026-07-09 14:08 UTC 左右）的状态是否正常

## 修复验证要求
无。此失败为 infra-error，不需要 code-fixer 进行代码修改。
