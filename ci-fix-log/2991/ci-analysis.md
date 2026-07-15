# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, MIRROR, FAILED, No more mirrors to try, dnf install

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
- 失败位置: `Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: openEuler 镜像站 `repo.openeuler.org` 的 HTTP/2 连接不稳定，多个 RPM 包（git-core、gcc-c++、guile）下载时出现 `Curl error (92): Stream error in the HTTP/2 framing layer`（HTTP/2 流未正常关闭，`INTERNAL_ERROR`），DNF 重试所有镜像后 `guile` 包下载失败，导致构建中断。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 仅新增了 `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`（安装 git、gcc、gcc-c++、make、cmake 并通过 cmake 构建 vvenc）以及更新 README、meta.yml、image-info.yml。失败发生在 DNF 从 `repo.openeuler.org` 下载依赖包阶段，属于 openEuler 官方镜像站 aarch64 仓库的 HTTP/2 服务端临时性问题，与 PR 代码逻辑无关。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 openEuler 镜像站 `repo.openeuler.org` 的 HTTP/2 服务端临时性故障，属于 CI 基础设施问题。重新触发 CI 构建（retry）大概率可以正常通过。

### 方向 2（置信度: 低，仅在方向 1 多次重试仍失败时考虑）
如果多次重试仍然失败，可在 Dockerfile 的 `dnf install` 命令中添加 `--setopt=timeout=60 --setopt=retries=5` 等重试参数，提高网络波动的容错性。但需注意，HTTP/2 流错误是服务端问题，客户端重试的缓解效果有限。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 CI 构建当时是否有服务端异常或网络抖动（可从 repo 运营方查证）
- 确认同一时段其他 PR 的 aarch64 构建是否也遇到相同问题，若普遍出现则为镜像站故障，可联系 openEuler 基础设施团队排查
- 确认 `guile`、`gcc-c++`、`git-core` 等包在 aarch64 仓库中的可用性和完整性
