# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF包下载网络异常
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, repo.openeuler.org

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6` — `RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`
- 失败原因: CI 在 aarch64 构建节点上执行 `dnf install` 时，`repo.openeuler.org` 镜像站返回 HTTP/2 流错误（Curl error 92），多个 RPM 包（`git-core`、`gcc-c++`）下载触发自动镜像重试后恢复，但 `guile` 包（git 的传递依赖）在所有镜像重试耗尽后仍下载失败，导致 dnf 退出码为 1。

### 与 PR 变更的关联

**无关。** PR 仅新增了一个标准格式的 Dockerfile（`Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`）及配套的 README.md、image-info.yml、meta.yml 更新。Dockerfile 中的 `dnf install` 命令（安装 git、gcc、gcc-c++、make、cmake）是该仓库同类 Dockerfile 的通用模式，不存在语法错误或依赖声明缺陷。失败完全由 `repo.openeuler.org` 镜像站在 aarch64 构建时间点上的 HTTP/2 流传输不稳定导致，与 PR 代码变更无因果关联。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 运行。** 此失败为 transient（暂时性）网络基础设施问题，`repo.openeuler.org` 在构建时刻对 aarch64 节点的 HTTP/2 连接不稳定。通常情况下，重新触发构建流水线即可通过（网络状态恢复后 rpm 包可正常下载）。Code Fixer 无需修改任何代码。

## 需要进一步确认的点

- 如果多次重试 CI 后仍然在同一包（guile）上失败，需排查 `repo.openeuler.org` 上 `guile-2.2.7-6.oe2403sp4.aarch64.rpm` 是否存在损坏或该文件在 CDN 边缘节点同步异常。
- 如果该仓库的其他 SP4 Dockerfile 在同一个 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上也出现类似的 HTTP/2 流错误，则可能是该 runner 到 `repo.openeuler.org` 的网络链路存在间歇性问题。
