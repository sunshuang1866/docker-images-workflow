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
#7 1709.7   guile-5:2.2.7-6.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: `dnf install` 从 `repo.openeuler.org` 下载 aarch64 RPM 包时，仓库服务器返回 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），多个包（`git-core`、`gcc-c++`、`guile`）均受影响，其中 `guile` 包在多次重试后耗尽所有镜像源，导致 dnf 安装失败退出。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了 vvenc 的 Dockerfile（`dnf install -y git gcc gcc-c++ make cmake`）、更新了 README.md、image-info.yml 和 meta.yml。构建在 Dockerfile 第 6 行（`dnf install` 基础系统依赖）就失败了，尚未到达 vvenc 源码编译阶段。失败根因是 openEuler 24.03-LTS-SP4 的 aarch64 RPM 仓库服务器（`repo.openeuler.org`）在构建时出现临时性 HTTP/2 协议故障，属于 CI 基础设施/上游仓库网络问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，触发重试即可**。该错误为上游 `repo.openeuler.org` 仓库服务器的临时性 HTTP/2 流中断，与 PR 的 Dockerfile 内容无关。对 CI 流水线执行 `recheck` 或重新触发构建，若仓库服务已恢复正常，则构建应能通过。Code Fixer 无需处理。

## 需要进一步确认的点
- 判断此次 `repo.openeuler.org` 的 HTTP/2 流错误是否为持续性问题。可以通过手动 `curl` 测试或查看同一时段其他使用 openEuler 24.03-LTS-SP4 仓库的 job 是否也失败来确认。
- 如果重试后仍然失败（说明仓库持续不可用），则需要联系 openEuler 基础设施团队排查 `repo.openeuler.org` 的 aarch64 仓库 HTTP/2 服务状态。
