# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, repo.openeuler.org

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
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上构建镜像时，`dnf install` 从 `repo.openeuler.org` 下载 RPM 包（git-core、gcc-c++、guile）过程中，openEuler 官方仓库服务器多次出现 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），最终 `guile` 包所有镜像重试均失败，导致整个 `dnf install` 步骤退出码为 1。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 vvenc 1.14.0 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中 `dnf install` 安装的是标准系统包（git、gcc、gcc-c++、make、cmake），失败发生在从 `repo.openeuler.org` 下载这些包的阶段。这是 openEuler 官方 aarch64 仓库的网络/服务器端基础设施问题，与 PR 代码变更毫无关联。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复，等待 CI 重试。** 这是一次性的网络/仓库服务器端故障（HTTP/2 流中断），与 PR 代码无关。建议：
- 手动重新触发 CI 构建（retry），大概率能通过。
- 若反复重试仍失败，需联系 openEuler 仓库维护团队检查 `repo.openeuler.org` 的 aarch64 镜像服务状态。

## 需要进一步确认的点
- `repo.openeuler.org` 在构建时刻（2026-07-09 14:08 UTC）的 aarch64 仓库服务是否存在已知故障或维护窗口。
- 如果多次重试均出现同类 HTTP/2 流错误，可能需要确认 runner 节点与 `repo.openeuler.org` 之间的网络链路是否存在 HTTP/2 协议兼容性问题。
