# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, dnf install

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
- 失败原因: dnf 从 `repo.openeuler.org` 下载 aarch64 架构 RPM 包时，HTTP/2 连接反复出现流错误（Curl error 92: INTERNAL_ERROR），多个包（git-core、gcc-c++、guile）下载重试失败，最终 guile 包所有镜像源耗尽，dnf 安装中止。

### 与 PR 变更的关联
**与 PR 改动无关。** PR 仅新增了一个标准 Dockerfile（`dnf install -y git gcc gcc-c++ make cmake` + 源码编译 vvenc），命令完全正常。失败根因在 `repo.openeuler.org` 仓库镜像站的 HTTP/2 服务端问题（针对 aarch64 架构的 OS 仓库），属于 CI 基础设施层面的网络/服务异常，重试构建可能即可通过。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 该失败为 `repo.openeuler.org` aarch64 仓库镜像的 HTTP/2 服务端瞬时故障（INTERNAL_ERROR），与代码变更无关。等待镜像站恢复后重新触发 CI 流水线，大概率可直接通过。

## 需要进一步确认的点
- 若多次重试仍失败，需确认 `repo.openeuler.org` 的 aarch64 OS 仓库是否持续不可用，或是否需要为 dnf 配置备用镜像源。
- 该失败仅发生在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`），x86_64 架构构建可能不受影响，需确认 x86_64 对应 job 是否已通过。
