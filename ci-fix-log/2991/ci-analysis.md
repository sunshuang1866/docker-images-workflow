# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, MIRROR, aarch64, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: CI 在 aarch64 runner 上构建时，`dnf install` 从 `repo.openeuler.org` 的 `openEuler-24.03-LTS-SP4/OS/aarch64/` 仓库下载多个 RPM 包（git-core、gcc-c++、guile）时遭遇 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR）。其中 git-core 经重试后成功，gcc-c++ 重试后仍失败，guile 耗尽所有镜像重试后最终失败，导致 dnf 安装步骤报 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 的变更（新增 Dockerfile、更新 README.md、image-info.yml、meta.yml）均为标准操作，Dockerfile 语法和逻辑正确。失败是 openEuler 官方仓库 `repo.openeuler.org` 在 aarch64 架构上的 HTTP/2 服务端问题导致的下载失败，属于 CI 基础设施/上游服务问题，在 x86_64 runner 上构建可能不会触发。

## 修复方向

### 方向 1（置信度: 高）
**重试触发 CI 重新构建。** 该失败是上游仓库 `repo.openeuler.org` 的 aarch64 HTTP/2 服务端临时性问题（`INTERNAL_ERROR`），非代码缺陷。等待仓库服务恢复后重新触发 CI 构建即可通过。若问题持续存在，可联系 openEuler 基础设施团队排查 repo 服务端 HTTP/2 配置。

### 方向 2（置信度: 低）
**降级为 HTTP/1.1 规避 HTTP/2 流错误。** 如果 repo.openeuler.org 的 HTTP/2 问题长期存在，可在 Dockerfile 的 `dnf install` 前通过 dnf 配置强制使用 HTTP/1.1（如设置 `http2=false` 或调整 libcurl 行为），绕过 HTTP/2 流层面的 INTERNAL_ERROR。但此方向为 workaround，不解决根本问题。

## 需要进一步确认的点
- 确认 x86_64 runner 上同 PR 的构建是否成功（日志中仅含 aarch64 job，x86_64 结果未知）
- 确认 `repo.openeuler.org` 在 aarch64 上的 HTTP/2 服务是否已恢复（可手动 `curl --http2` 测试）
- 若多次重试 CI 仍失败，需排查 openEuler 24.03-LTS-SP4 aarch64 仓库的 CDN/服务器端配置
