# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: dnf 下载 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), HTTP/2 stream, INTERNAL_ERROR, dnf install, No more mirrors to try, repo.openeuler.org

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
- 失败原因: CI aarch64 runner 在通过 `dnf` 从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 的 RPM 包时，`repo.openeuler.org` 服务器的 HTTP/2 连接反复出现流错误（Curl error 92: HTTP/2 stream INTERNAL_ERROR），其中 `git-core` 和 `gcc-c++` 经多次重试后成功下载，但 `guile` 包在所有镜像均尝试完毕后仍无法下载，导致 dnf 安装阶段失败。

### 与 PR 变更的关联
此次失败与 PR 的代码变更**无关联**。PR 新增的 Dockerfile 中 `dnf install` 命令完全正确（安装 git、gcc、gcc-c++、make、cmake 五个标准编译依赖），没有语法错误或版本问题。失败根因是 CI 构建节点的 `repo.openeuler.org` 镜像站 HTTPS/2 连接不稳定，属于纯基础设施/网络波动问题。`git-core` 和 `gcc-c++` 也遇到了同样的 Curl error (92)，只是它们通过重试恢复了，而 `guile` 的重试次数耗尽才最终失败。

## 修复方向

### 方向 1（置信度: 低 — 此为 infra-error，建议重试）
该失败为 CI 基础设施网络波动所致，与 PR 代码无关。建议触发 CI 重新构建（rerun），大概率能通过。如果反复出现同样的 HTTP/2 流错误，则需联系 openEuler 镜像站管理员排查 `repo.openeuler.org` 的 HTTP/2 服务端配置或 CDN 节点健康状况。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在构建时刻是否存在 HTTP/2 服务降级或不稳定情况
- 如果该问题在该 PR 上反复复现（且仅 aarch64 构建失败），可能需要验证 openEuler 24.03-LTS-SP4 的 aarch64 仓库包完整性，确认 `guile-2.2.7-6.oe2403sp4.aarch64.rpm` 是否在源站上存在且可正常下载
