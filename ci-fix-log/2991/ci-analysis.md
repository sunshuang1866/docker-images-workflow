# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: repo 镜像 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, dnf install

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: openEuler 24.03-LTS-SP4 的官方镜像仓库 `repo.openeuler.org` 在 CI 构建期间出现 HTTP/2 流错误（Curl error 92），导致多个 RPM 包（`git-core`、`gcc-c++`、`guile`）下载失败，最终 `guile` 包在所有镜像重试后仍无法下载，`dnf install` 以 exit code 1 失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 的变更仅为：
1. 新增 vvenc 1.14.0 在 openEuler 24.03-lts-sp4 上的 Dockerfile（内容为标准 `dnf install` + cmake 构建流程）
2. 更新 README.md 添加新镜像标签说明
3. 更新 image-info.yml 添加新标签条目
4. 更新 meta.yml 添加版本→路径映射

失败发生在 Dockerfile 的第一个 `RUN` 指令（`dnf install` 阶段），且错误为 `repo.openeuler.org` 的 HTTP/2 传输层错误，属于 CI 构建时镜像仓库侧的网络基础设施问题。多个不同的 RPM 包均报相同的 `Curl error (92): Stream error in the HTTP/2 framing layer`，说明问题在仓库服务端而非客户端或 Dockerfile 配置。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码，等待仓库恢复后重试 CI。**

这是一个纯粹的 CI 基础设施问题：`repo.openeuler.org` 的 aarch64 软件包仓库在构建期间 HTTP/2 传输不稳定，导致多个 RPM 包下载失败。Dockerfile 内容本身没有问题（`dnf install` 命令语法正确、包名均存在且依赖解析成功）。建议重新触发 CI build，若仓库服务已恢复则构建可通过。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 openEuler-24.03-LTS-SP4 aarch64 仓库当前是否已恢复正常服务
- 如果反复重试仍出现同样的 HTTP/2 错误，考虑在 Dockerfile 的 `dnf install` 前添加 `echo "http2=false" >> /etc/dnf/dnf.conf`（降级到 HTTP/1.1）或配置其他镜像源（如镜像站）作为备选
