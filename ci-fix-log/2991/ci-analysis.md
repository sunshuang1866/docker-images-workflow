# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
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
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: CI 在 aarch64 runner 上构建时，`dnf install` 从 `repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/` 下载 RPM 包过程中，多个包（`git-core`、`gcc-c++`、`guile`）遇到 HTTP/2 帧层流错误（Curl error 92: INTERNAL_ERROR），最终 `guile` 包耗尽所有镜像源，导致 `dnf install` 失败退出。此为 openEuler 24.03-LTS-SP4 aarch64 仓库服务端的 HTTP/2 协议层基础设施问题，与 PR 代码变更无关。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了 Dockerfile（标准 `dnf install` + `cmake` 构建流程）及配套的 README、image-info.yml、meta.yml 文档条目。Dockerfile 中的 `dnf install` 命令本身语法正确，所列包名均为 openEuler 24.03-LTS-SP4 仓库中存在的标准包。失败直接原因是 openEuler 仓库 aarch64 端的 HTTP/2 服务不稳定，重试即可通过。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试。** 该失败为 openEuler 24.03-LTS-SP4 aarch64 仓库的临时性 HTTP/2 网络问题，无需修改任何代码或 Dockerfile。直接重新触发 CI 构建，待仓库端网络恢复后即可通过。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 aarch64 仓库（`repo.openeuler.org`）的 HTTP/2 服务是否已恢复正常。
- 如多次重试仍失败，需排查是否该仓库对特定 IP 段或请求频率有限制策略。
