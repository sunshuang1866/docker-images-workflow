# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2传输中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf download

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 1709.7   guile-5:2.2.7-6.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all` 步骤）
- 失败原因: `repo.openeuler.org` 仓库在 aarch64 构建节点上为 SP4 的 OS 源提供 RPM 包下载时，HTTP/2 传输层出现多次 `INTERNAL_ERROR` 流错误（Curl error 92），导致 `git-core`、`gcc-c++` 重试后恢复，但 `guile` 包在所有镜像重试耗尽后仍下载失败，dnf 安装链路中断，Docker build 退出码为 1。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了一个标准的 Dockerfile（安装 git、gcc、gcc-c++、make、cmake 后编译 vvenc），Dockerfile 本身没有问题。失败发生在 `dnf install` 阶段，是 openEuler 24.03-LTS-SP4 的 aarch64 软件仓库在 CI 构建期间的 HTTP/2 传输层不稳定所致，属于基础设施层面的临时性问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修改。** 这是 CI 基础设施问题——`repo.openeuler.org` 的 aarch64 SP4 仓库在构建时 HTTP/2 CDN 传输出现间歇性中断。属于网络/仓库侧临时波动，建议直接重试 CI job，大概率可通过。

### 方向 2（置信度: 低，备选）
如果多次重试均失败，可在 Dockerfile 的 `dnf install` 命令前添加 `dnf makecache` 或尝试在 `/etc/dnf/dnf.conf` 中追加 `max_parallel_downloads=1` 和 `retries=10` 来降低并发度并增加重试次数。但此方案属于治标，根因仍在仓库侧。

## 需要进一步确认的点
- 在同一时间段内，其他 aarch64 SP4 的 PR 构建是否也出现了同样的 HTTP/2 流错误？如果存在共性，说明 `repo.openeuler.org` 的 aarch64 CDN/源服务器在该时段存在稳定性问题。
- `git-core` 和 `gcc-c++` 虽然报 `[MIRROR]` 错误但最终重试成功（日志中可见后续包下载继续），仅 `guile` 最终耗尽镜像。检查是否特定于 `guile` 包的 CDN 节点存在问题。

## 修复验证要求
不适用（infra-error，无需代码修复）。
