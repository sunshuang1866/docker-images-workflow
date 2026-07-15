# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, No more mirrors to try

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
- 失败原因: CI 构建节点（aarch64 runner `ecs-build-docker-aarch64-04-sp`）在通过 `dnf install` 从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 的 RPM 包时，多个包（`git-core`、`gcc-c++`、`guile`）均遭遇 HTTP/2 传输层流错误（`Curl error (92)`），其中 `gcc-c++` 两次重试均失败，`guile` 耗尽所有镜像后安装中断，导致整个构建失败。

### 与 PR 变更的关联
**与 PR 无关。** PR #2991 仅新增了 vvenc 1.14.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 和配套元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 本身内容为标准的 dnf 安装构建工具 + git clone + cmake 编译流程，未引入任何自定义下载逻辑、网络配置或第三方源。失败发生在 `dnf install` 从 openEuler 官方仓库拉取基础系统包（git、gcc、gcc-c++、cmake 等）阶段，属于 CI 基础设施与上游仓库之间的网络传输问题。

## 修复方向

### 方向 1（置信度: 中）
**重试构建**。HTTP/2 流错误（`INTERNAL_ERROR (err 2)`）通常是 `repo.openeuler.org` 服务器端或中间网络设备的瞬时问题。多次数据包下载遭遇相同的传输层错误表明问题可能出现在：
- openEuler 镜像站 CDN/反向代理节点的 HTTP/2 实现存在间歇性 bug
- CI 构建节点与仓库之间的网络路径上存在 HTTP/2 不兼容的中间设备

Code Fixer 无需修改代码，直接重新触发 CI 构建即可。若重试后仍反复出现同类问题，需联系 openEuler 基础设施团队排查 `repo.openeuler.org` 的 HTTP/2 服务稳定性。

### 方向 2（置信度: 低）
**强制 dnf 使用 HTTP/1.1**。如果问题持续复现，可在 Dockerfile 的 dnf 命令前设置环境变量禁用 HTTP/2，规避传输层问题：
- 在 `RUN` 中设置 `echo "http2=false" >> /etc/dnf/dnf.conf` 或在命令行前加 `http_proxy` 相关配置
- 此方向仅作为临时规避方案，不应作为长期修复

## 需要进一步确认的点
1. 该失败是否为 aarch64 架构独有，x86-64 节点是否也遭遇了同样的 HTTP/2 流错误？（当前日志仅包含 aarch64 runner 的输出）
2. `repo.openeuler.org` 的 HTTP/2 服务是否存在已知的稳定性问题或近期变更？
3. 同一时间段内，其他同样依赖 `repo.openeuler.org` 的 PR 构建是否也出现了类似的 Curl error (92)？
4. 确认 `guile` 包失败前，`gcc-c++` 包是否已耗尽重试次数并被放弃——若 `gcc-c++` 是 `gcc-c++` 的直接安装依赖（而非间接依赖），即使 `guile` 下载成功，`gcc-c++` 的失败也会导致最终构建失败。

## 修复验证要求
无需验证——此为 infra-error，Code Fixer 无需修改代码。建议直接重新触发 CI 构建。
