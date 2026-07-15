# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Stream error, INTERNAL_ERROR, repo.openeuler.org, No more mirrors to try, dnf download packages

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
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上构建时，`dnf install` 从 `repo.openeuler.org` 下载多个 RPM 包（git-core、gcc-c++、guile）时遭遇 HTTP/2 流错误（Curl error 92: Stream error in the HTTP/2 framing layer），所有重试耗尽后 `guile-2.2.7-6.oe2403sp4.aarch64.rpm` 仍下载失败，导致 `dnf install` 以 exit code 1 退出。根因是 openEuler 官方 RPM 镜像站 `repo.openeuler.org` 的 HTTP/2 服务端在构建时段不稳定，与 PR 代码变更完全无关。

### 与 PR 变更的关联
PR 仅新增了 vvenc 1.14.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 以及配套的 README.md、image-info.yml、meta.yml 元数据更新。Dockerfile 中的 `dnf install` 命令写法与同类镜像（如 24.03-lts-sp3 版本）一致，无语法错误。本次失败纯属 CI 构建时的网络基础设施问题，与 PR 改动无关。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 失败原因为 `repo.openeuler.org` 在 aarch64 构建时段出现 HTTP/2 流不稳定，导致 RPM 包下载失败。Code Fixer 无需处理此 PR。建议在 CI 中重新触发构建（retry），等待镜像站恢复后构建即可通过。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 当前是否已恢复正常（可在浏览器或 CI 环境中直接 wget 测试上述失败 URL）
- 如果反复重试仍失败，考虑是否为 aarch64 runner 所在网络与 `repo.openeuler.org` 之间存在持续的网络连通性问题
- 可检查同一时段其他 openEuler 24.03-LTS-SP4 镜像的 CI 构建是否也出现了相同的 HTTP/2 错误，以确认是否为通用 mirror 故障
