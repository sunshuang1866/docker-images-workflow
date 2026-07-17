# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, repo.openeuler.org, dnf install

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上构建时，`repo.openeuler.org` 的 HTTP/2 CDN 服务发生流错误，多个 RPM 包（`git-core`、`gcc-c++`、`guile`）下载均出现 `Curl error (92): Stream error in the HTTP/2 framing layer`。其中 `git-core` 和 `gcc-c++` 经重试后下载成功，但 `guile` 尝试了所有镜像均失败，导致 `dnf install` 整体失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 此次 PR 仅新增了一个标准化的 Dockerfile（13 行），其中 `RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all` 是项目中大量 Dockerfile 共同使用的通用依赖安装模式。失败根因为 `repo.openeuler.org` 仓库在 aarch64 架构上的 HTTP/2 服务端流错误，属于 CI 基础设施/网络问题，非代码缺陷。`git-core` 和 `gcc-c++` 也遭遇了同样的 HTTP/2 流错误（仅因重试才成功），进一步佐证这是仓库服务端问题而非单个包的版本或可用性问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是一个临时性的 `repo.openeuler.org` 仓库 HTTP/2 基础设施故障。应在 CI 构建环境网络恢复后重试构建（re-trigger CI），预期可通过。如果该问题持续出现，可考虑在 Dockerfile 中配置 dnf 的 HTTP/2 行为（如通过 `/etc/dnf/dnf.conf` 设置 `http2=false` 降级到 HTTP/1.1）或添加备用镜像源，但这属于对仓库基础设施问题的规避性措施，而非对 PR 代码的修复。

## 需要进一步确认的点
- `repo.openeuler.org` 的 OpenEuler-24.03-LTS-SP4/aarch64 仓库 CDN 是否在此期间存在已知故障或维护窗口。
- 该故障是偶发性还是持续性：可通过 re-trigger CI 或同时段其他 aarch64 构建 job 的成败情况来验证。
- 若问题持续，可能需要联系 openEuler 基础设施团队排查 `repo.openeuler.org` 的 HTTP/2 CDN 配置。
