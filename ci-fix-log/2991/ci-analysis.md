# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install, repo.openeuler.org

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
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 `dnf install` 时，从 `repo.openeuler.org` 下载 RPM 包过程中遭遇 HTTP/2 协议层流错误（Curl error 92: `INTERNAL_ERROR`），多个核心包（`git-core`、`gcc-c++`、`guile`）均受波及。虽然 git-core 和 gcc-c++ 通过镜像重试机制成功下载，但 `guile` 包在所有镜像重试后仍失败，导致 `dnf install` 整体退出码为 1，构建中断。

### 与 PR 变更的关联
**无关。** 本次 PR 新增的 Dockerfile 仅包含标准的 `dnf install -y git gcc gcc-c++ make cmake` 命令，无语法错误或版本冲突。失败完全由 `repo.openeuler.org` 服务器端 HTTP/2 连接异常引起，属于 CI 基础设施层面的瞬时网络故障。同类问题在 git-core 和 gcc-c++ 下载中也被观测到（均出现相同的 Curl error 92），进一步印证这是上游仓库服务端而非客户端的问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复，触发 CI 重试即可。** 该失败为 `repo.openeuler.org` 仓库服务器瞬时 HTTP/2 协议层故障，与 PR 的代码变更无关。`dnf` 的镜像重试机制已自动恢复部分受影响包（git-core、gcc-c++）的下载，仅 guile 的重试次数耗尽。重新触发 CI 构建（retrigger）大概率可成功通过。

### 方向 2（置信度: 低）
若重试仍反复失败，可能是 `repo.openeuler.org` 的 aarch64 仓库存在持续性问题。此时可考虑在 Dockerfile 中为 `dnf` 添加 `--setopt=retries=10` 增加重试次数，或等待上游仓库恢复。但这属于临时绕过手段，不建议用于生产 Dockerfile。

## 需要进一步确认的点
- 确认 `repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/` 仓库在当前时段的服务状态是否稳定。
- 确认 CI aarch64 runner (`ecs-build-docker-aarch64-04-sp`) 到 `repo.openeuler.org` 的网络链路是否存在持续性问题。
- 若同一时段其他 PR 的 aarch64 构建也出现同等错误，可进一步确认为上游服务端问题。
