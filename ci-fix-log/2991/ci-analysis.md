# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 1709.7   guile-5:2.2.7-6.oe2403sp4: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: `repo.openeuler.org` 在向 aarch64 构建节点提供 openEuler 24.03-LTS-SP4 仓库的 RPM 包时，HTTP/2 流反复出现 `INTERNAL_ERROR (err 2)`，多个包（git-core、gcc-c++、guile）的下载均受到 HTTP/2 流错误影响，其中 `guile` 包（git 的传递依赖）在重试耗尽所有镜像后最终下载失败，导致 `dnf install` 以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了一个标准的 Dockerfile（`dnf install -y git gcc gcc-c++ make cmake`），Dockerfile 本身的语法和内容无误。失败的根本原因是 `repo.openeuler.org` 镜像站服务器的 HTTP/2 实现问题，属于 CI 基础设施层面的网络故障。该 `dnf install` 步骤未引用任何来自 PR 变更的自定义源或特殊参数，完全是基础设施问题。

构建节点信息：`ecs-build-docker-aarch64-04-sp (docker-build-aarch64)`，仅影响 aarch64 架构。

## 修复方向

### 方向 1（置信度: 低）
**重试构建。** 此错误本质上是 `repo.openeuler.org` 镜像站 HTTP/2 服务的瞬时故障，最直接的修复方式是重新触发 CI 构建。如果镜像站已恢复，下一次构建可正常通过。该方向无需对代码做任何修改。

### 方向 2（置信度: 低）
**在 Dockerfile 中将 dnf 降级为 HTTP/1.1。** 在 `dnf install` 之前设置 `echo "http2=false" >> /etc/dnf/dnf.conf` 或等效配置，使 dnf/libcurl 使用 HTTP/1.1 而非 HTTP/2 连接仓库。此方法可规避镜像站 HTTP/2 实现缺陷，但会牺牲 HTTP/2 的性能优势，且属于绕过而非修复基础设施问题。

## 需要进一步确认的点
1. `repo.openeuler.org` 对 openEuler 24.03-LTS-SP4 aarch64 仓库的 HTTP/2 服务是否为持续性问题（需要检查同一时间段内其他使用 24.03-lts-sp4 aarch64 构建的 job 是否也失败）。
2. 该故障是否仅影响 aarch64 架构的构建节点（x86_64 构建是否正常）。
3. 镜像站维护方是否有已知的 HTTP/2 服务问题公告。
