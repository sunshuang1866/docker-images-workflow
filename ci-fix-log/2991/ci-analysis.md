# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像源HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install, repo.openeuler.org

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
- 失败原因: openEuler 24.03-LTS-SP4 的 `repo.openeuler.org` 镜像仓库在 aarch64 runner 上对多个 RPM 包（git-core、gcc-c++、guile）返回 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），dns 重试所有镜像后仍无法下载 `guile` 包，导致 `dnf install` 失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 新增的 Dockerfile 中 `dnf install` 命令语法正确、包名有效（`git gcc gcc-c++ make cmake` 均为 openEuler 标准软件包），日志中 `Dependencies resolved` 阶段已正确解析出 156 个依赖包，失败纯粹是 `repo.openeuler.org` 仓库的网络/服务端问题。同一 Dockerfile 在其他时间段重试构建大概率成功。

## 修复方向

### 方向 1（置信度: 高）
无需修改 Dockerfile 或任何代码。这是 openEuler 镜像仓库 `repo.openeuler.org` 的临时性网络/服务端问题（HTTP/2 framing layer 异常），可通过 **重试 CI 构建** 解决。Code Fixer 无需处理。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 aarch64 架构仓库当前状态是否正常（可手动 wget 测试 `guile-2.2.7-6.oe2403sp4.aarch64.rpm` 是否可下载）。
- 确认该仓库是否在特定时段存在 HTTP/2 协议层不稳定的已知问题，必要时可考虑在 Dockerfile 中为 `dnf` 添加重试选项或降级到 HTTP/1.1。
