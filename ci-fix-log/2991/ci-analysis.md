# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR (err 2), repo.openeuler.org, dnf install

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
- 失败原因: CI 在 aarch64 节点（`ecs-build-docker-aarch64-04-sp`）上构建时，`dnf install` 从 `repo.openeuler.org` 下载 RPM 包（git-core、gcc-c++、guile）过程中，openEuler 镜像站的 HTTP/2 服务器多次返回流错误（Curl error 92: INTERNAL_ERROR），导致多个包下载失败，guile 包所有镜像均尝试失败后 dnf 退出码为 1。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了一个标准的 vvenc Dockerfile（安装 git/gcc/gcc-c++/make/cmake 后编译源码），Dockerfile 语法和内容均无问题。失败完全由 `repo.openeuler.org` 镜像站在 aarch64 架构上的 HTTP/2 服务端问题引起，属于 CI 基础设施层面的瞬时故障。日志中可见 4 个不同的 RPM 包（git-core、gcc-c++ 两次、guile）均因相同的 HTTP/2 流错误而下载失败，进一步证实是服务端问题而非特定包被删除或 URL 错误。

## 修复方向

### 方向 1（置信度: 高）
**重试构建。** 该失败是 `repo.openeuler.org` 镜像站的 HTTP/2 服务端瞬时故障（Curl error 92: INTERNAL_ERROR），与 PR 代码无关。等待镜像站服务恢复后重新触发 CI 构建即可。无需对 Dockerfile 做任何修改。

### 方向 2（置信度: 低）
若镜像站持续不稳定，可考虑在 Dockerfile 中为 `dnf install` 添加重试机制（如 `dnf install -y --setopt=retries=5 ...`），但这不是根因修复，仅为网络波动容错增强。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 镜像站 aarch64 仓库的服务状态是否已恢复（可直接用 curl 测试下载任一 RPM 包）
- 若重试后仍失败，需确认是否 openEuler 24.03-LTS-SP4 的 aarch64 仓库镜像同步存在问题

## 修复验证要求
无需修复验证。该失败为 infra-error，Code Fixer 无需处理任何代码。
