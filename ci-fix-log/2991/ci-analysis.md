# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf, Error downloading packages

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install ...` 步骤）
- 失败原因: CI 构建节点（aarch64）通过 `dnf` 从 `repo.openeuler.org` 下载 RPM 包时，HTTP/2 连接多次出现 `INTERNAL_ERROR (err 2)` 流错误，3 个包（git-core、gcc-c++、guile）受影响，其中 git-core 和 gcc-c++ 经重试后成功，guile 包的重试次数耗尽后失败，导致整个 `dnf install` 命令退出码为 1。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 的改动仅为新增 vvenc 1.14.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `dnf install` 命令语法和包列表均正确无误。失败发生在基础设施层——`repo.openeuler.org` 的 aarch64 仓库 HTTP/2 连接不稳定，属于 CI 构建环境的网络问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 这是 CI 基础设施的网络瞬时故障，`repo.openeuler.org` 的 aarch64 HTTP/2 端点当时不稳定。直接重新触发 CI 构建（re-run/retry）即可，大概率会成功。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 aarch64 仓库当前是否稳定（可在浏览器或本地环境测试下载对应 RPM 包的连通性）。
- 如果多次重试仍出现同类 HTTP/2 错误，需联系 openEuler 基础设施团队排查 `repo.openeuler.org` 的 HTTP/2 服务器配置或 CDN 节点健康状态。

## 修复验证要求
（不适用——本次失败为 infra-error，与 Dagger 代码无关，无需 code-fixer 介入修改。）
