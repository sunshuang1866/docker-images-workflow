# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, repo.openeuler.org

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

Dockerfile:6
---
   6 | >>> RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all
---
ERROR: failed to solve: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上构建镜像时，`dnf install` 从 `repo.openeuler.org` 下载多个 RPM 包（git-core、gcc-c++、guile）时遭遇 HTTP/2 连接层错误（Curl error 92: INTERNAL_ERROR），重试所有镜像源后仍失败，导致构建终止。

### 与 PR 变更的关联
**与 PR 改动无关。** 本次 PR 仅新增了一个标准的 vvenc Dockerfile（dnf 安装 git/gcc/gcc-c++/make/cmake → git clone → cmake 构建），Dockerfile 本身语法和逻辑均正确。失败完全由 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库在网络传输层面（HTTP/2 stream error）不稳定导致，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 低）
**重试构建**：该错误为网络层面的暂态故障（HTTP/2 stream not closed cleanly），可能在下一次 CI 触发时自动恢复。建议直接 re-run 本次 CI job。

### 方向 2（置信度: 低）
**在 Dockerfile 中为 dnf 配置本地镜像源**：将 `repo.openeuler.org` 替换为更稳定的 openEuler 镜像站（如华为云镜像 `repo.huaweicloud.com/openeuler`），通过 `sed` 在 `dnf install` 前修改 `/etc/yum.repos.d/` 中的 repo 文件，降低对单一上游仓库的依赖。但需注意：此方案仅在 `repo.openeuler.org` 持续不可用时才有意义，且属于非标准实践。

## 需要进一步确认的点
- `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库当前是否普遍存在 HTTP/2 连接问题，还是仅对特定 CI runner 节点 `ecs-build-docker-aarch64-04-sp` 的网络路径不畅通。
- 同一 PR 的 x86_64 架构构建是否成功（日志中仅包含 aarch64 job 的输出，若 x86_64 构建成功则进一步印证该问题为 aarch64 仓库/网络侧暂态故障）。
- 其他使用 openEuler 24.03-LTS-SP4 aarch64 基础镜像的 PR 是否同时出现类似 dnf 下载失败。
