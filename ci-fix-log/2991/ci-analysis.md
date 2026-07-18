# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, dnf install, repo.openeuler.org

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
- 失败原因: CI 构建节点 `ecs-build-docker-aarch64-04-sp`（aarch64）在执行 `dnf install` 从 `repo.openeuler.org` 下载 RPM 包时，多个包（`git-core`、`gcc-c++`、`guile`）遭遇 HTTP/2 流传输中断错误（Curl error 92: INTERNAL_ERROR），其中 `gcc-c++` 重复失败 2 次、`guile` 重试耗尽后最终导致构建失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 仅新增了一个标准的 vvenc Dockerfile（安装 git、gcc、gcc-c++、make、cmake 并通过 cmake 编译 vvenc），同时更新了 README.md、image-info.yml 和 meta.yml。`dnf install` 下载 RPM 包失败是 `repo.openeuler.org` 仓库镜像与 CI aarch64 构建节点之间的网络传输问题（HTTP/2 流异常中断），属于 CI 基础设施层面的临时性故障，非 PR 代码缺陷。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 该失败为 `repo.openeuler.org` 仓库到 CI aarch64 runner 的网络波动导致的临时性 RPM 下载失败（HTTP/2 流中断），与 PR 代码变更完全无关。直接重试 CI 即可，若网络恢复则构建将正常通过。

### 方向 2（置信度: 低）
如果多次重试仍失败，可能是 openEuler 24.03-LTS-SP4 的 aarch64 仓库镜像站 `repo.openeuler.org` 存在持续的服务端 HTTP/2 问题，可尝试在 Dockerfile 的 `dnf install` 前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 强制 dnf 使用 HTTP/1.1 协议下载，规避 HTTP/2 流中断问题。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 openEuler-24.03-LTS-SP4 aarch64 仓库当前是否稳定可访问，是否存在 HTTP/2 服务端问题
- 确认 x86-64 架构的构建 job 是否也出现相同的 RPM 下载失败（本次日志仅包含 aarch64 构建 job）
- 如果其他 SP4 镜像的 aarch64 构建也同时失败，可确认是仓库侧问题而非单次网络抖动
