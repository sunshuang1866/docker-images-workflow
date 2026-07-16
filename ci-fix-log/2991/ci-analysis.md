# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, No more mirrors to try, INTERNAL_ERROR, dnf, repo.openeuler.org

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
- 失败原因: aarch64 构建节点在执行 `dnf install -y git gcc gcc-c++ make cmake` 时，从 `repo.openeuler.org` 下载多个 RPM 包（git-core、gcc-c++、guile）均遭遇 HTTP/2 流错误（Curl error 92: `HTTP/2 stream was not closed cleanly: INTERNAL_ERROR`）。虽然 git-core 和 gcc-c++ 后续重试成功，但 guile 包在耗尽所有镜像重试后仍失败，导致 dnf 安装步骤整体失败。

### 与 PR 变更的关联
- **无关**。PR 仅新增了一个标准的 Dockerfile（vvenc 1.14.0 on openEuler 24.03-LTS-SP4），其 `dnf install` 命令为常规包安装操作，Dockerfile 本身无任何语法或逻辑错误。
- 失败的直接原因是 openEuler 官方软件仓库（`repo.openeuler.org`）在 aarch64 构建节点上的 HTTP/2 传输不稳定，多次出现 `INTERNAL_ERROR (err 2)` 流中断。
- 构建在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行，该架构的 RPM 包下载路径受影响。

## 修复方向

### 方向 1（置信度: 高）
- 触发 CI 重新构建。HTTP/2 流错误本质上是上游仓库服务器的瞬时网络/协议问题，重新触发构建大概率可以正常通过。从日志中 git-core（先失败后成功）和 gcc-c++（先失败后仍在重试）的行为来看，该问题呈间歇性特征。

### 方向 2（置信度: 中）
- 若重试后仍然失败，可在 Dockerfile 的 `dnf install` 前增加 `dnf update --refresh -y` 刷新元数据缓存，或在 `/etc/dnf/dnf.conf` 中添加 `max_parallel_downloads=1` 降低并发连接数，减少 HTTP/2 多路复用争用触发 `INTERNAL_ERROR` 的概率。

### 方向 3（置信度: 低）
- 在 Dockerfile 中将 `dnf install` 的镜像源临时切换为非 HTTP/2 端点或使用 `http://` 协议，强制 curl 使用 HTTP/1.1 传输，绕过 HTTP/2 流错误。此方向需要确认 openEuler 仓库是否提供 HTTP/1.1 或非 HTTP/2 端点。

## 需要进一步确认的点
1. `repo.openeuler.org` 的 HTTP/2 服务器配置是否存在已知问题——该错误是否在近期多个 PR 的 aarch64 构建中频繁出现。
2. 构建节点 `ecs-build-docker-aarch64-04-sp` 到 `repo.openeuler.org` 之间的网络链路上是否存在 HTTP/2 流中断的中间设备（如代理、负载均衡器）。
3. 其他同类 PR（新增其他镜像的 SP4 支持）在 aarch64 runner 上是否也遇到相同错误，以判断这是偶发事件还是系统性故障。
