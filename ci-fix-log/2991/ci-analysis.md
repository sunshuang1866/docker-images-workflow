# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, MIRROR, No more mirrors to try, repo.openeuler.org

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
- 失败位置: Dockerfile:6 — `RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 `dnf install` 时，从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 的 aarch64 RPM 包时遭遇 HTTP/2 协议层错误（Curl error 92: Stream error, INTERNAL_ERROR），多个包（git-core、gcc-c++、guile）下载失败，重试全部镜像后端后仍不可用，导致 dnf 安装步骤整体失败。

### 与 PR 变更的关联
**与 PR 代码变更无关**。PR 变更仅新增了一个标准的 vvenc Dockerfile（安装 git、gcc、gcc-c++、make、cmake）及配套的 README、image-info.yml、meta.yml 条目。`dnf install` 命令本身完全正确，失败源于 openEuler 24.03-LTS-SP4 的 aarch64 包仓库服务器端 HTTP/2 流传输异常，属于 CI 基础设施/仓库服务端问题，Code Fixer 无需处理。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 此为 `repo.openeuler.org` 服务器端 HTTP/2 协议层故障，应等待仓库基础设施恢复后重新触发 CI 构建。如果该问题持续出现，可由 CI 运维方考虑：
- 为 `dnf` 配置 HTTP/1.1 回退（禁用 HTTP/2）以绕过服务端 HTTP/2 实现缺陷
- 或切换至 openEuler 镜像站的其他镜像节点

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 aarch64 24.03-LTS-SP4 仓库当前是否处于维护或异常状态
- 如果 x86_64 架构的构建也使用了相同的 SP4 仓库，其是否也出现同类 HTTP/2 错误（当前日志仅有 aarch64 runner 的输出）
- 如该问题仅影响 aarch64 且持续复现，建议 CI 团队排查仓库服务器的 HTTP/2 配置或 aarch64 节点的网络路径
