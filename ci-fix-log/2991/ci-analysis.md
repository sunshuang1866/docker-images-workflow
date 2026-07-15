# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, MIRROR, dnf install, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 `dnf install` 时，`repo.openeuler.org` 的 openEuler-24.03-LTS-SP4 aarch64 仓库在 HTTP/2 传输层出现多次 `INTERNAL_ERROR` 流帧错误（Curl error 92），导致 git-core、gcc-c++、guile 三个 RPM 包下载失败。其中 git-core 和 gcc-c++ 经重试后恢复，guile 耗尽所有镜像重试后最终失败，dnf 退出码为 1。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 仅新增了标准的 `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`（包含标准 `dnf install` 命令）、更新了 README.md、image-info.yml 和 meta.yml。Dockerfile 中的 `dnf install -y git gcc gcc-c++ make cmake` 命令语法完全正确，失败纯粹由 openEuler SP4 aarch64 软件仓库的网络传输层不稳定导致。日志显示部分包（如 acl、cmake、binutils、dbus 等）下载成功，说明仓库元数据可达，但特定大文件在传输过程中遭遇 HTTP/2 协议异常。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 此失败为 CI 基础设施网络问题（`repo.openeuler.org` HTTP/2 流传输异常），属于暂态性故障。建议触发重试（re-run CI job），等待仓库网络恢复正常后构建应能通过。

### 方向 2（置信度: 低）
如果多次重试仍然失败且仅发生在 aarch64 架构上，可能是 openEuler 24.03-LTS-SP4 aarch64 仓库的特定 RPM 包存在服务端问题。此时需要联系 openEuler 基础设施团队排查 `repo.openeuler.org` 上 SP4 aarch64 仓库中 git-core、gcc-c++、guile 三个包的服务端 HTTP/2 配置。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 CI 构建时间段（2026-07-09 14:09 UTC）是否存在 aarch64 仓库的 HTTP/2 服务异常。
- 如果后续重试仍然失败，需确认是否是 openEuler 24.03-LTS-SP4 aarch64 仓库本身存在包缺失或损坏问题（而非纯网络问题）。
- 确认 x86_64 对应的 SP4 job 是否也遇到相同问题，以判断是否架构特有问题。
