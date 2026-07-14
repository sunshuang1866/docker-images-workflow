# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, repo.openeuler.org

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
- 失败原因: CI 构建环境（aarch64 runner `ecs-build-docker-aarch64-04-sp`）在 `dnf install` 阶段从 `repo.openeuler.org` 下载 RPM 包时，多个包（`git-core`、`gcc-c++`、`guile`）遭遇 HTTP/2 流帧层错误（Curl error 92: INTERNAL_ERROR），其中 `guile` 包在所有镜像源均重试失败后导致 `dnf` 安装整体失败。这是 `repo.openeuler.org` 镜像站/反向代理层在 HTTP/2 传输过程中发生的临时性基础设施故障。

### 与 PR 变更的关联
**与 PR 无关。** PR 的变更仅限于新增 vvenc Dockerfile、更新 README.md、image-info.yml 和 meta.yml，代码内容无问题。失败发生在 `dnf install` 包下载阶段，是 `repo.openeuler.org` 仓库镜像服务的 HTTP/2 传输错误，属于 CI 基础设施层面的临时故障，与 Dockerfile 内容或 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 该失败为 CI 基础设施问题（`repo.openeuler.org` 镜像站在构建时段出现 HTTP/2 流传输错误）。Code Fixer 无需任何操作，建议触发 CI 重试（retry/rerun）即可。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` CDN/反向代理在失败时段是否存在已知的 HTTP/2 相关故障或负载异常。
- 若该问题持续复现，考虑在 CI 构建脚本中为 `dnf` 添加重试机制（如 `dnf install --setopt=retries=10 ...`）以提高网络波动环境下的鲁棒性。
