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
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 `dnf install` 时，`repo.openeuler.org` 仓库服务器的 HTTP/2 连接反复出现流传输错误（`INTERNAL_ERROR`），导致 `gcc-c++`、`git-core` 等包的下载多次重试后部分成功，但 `guile` 包在耗尽所有镜像重试后仍下载失败，最终 `dnf` 以 exit code 1 退出。

### 与 PR 变更的关联

**与 PR 变更无关。** 本次 PR 仅新增了一个标准 Dockerfile（`Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`），包含常规的 `dnf install -y git gcc gcc-c++ make cmake` 命令。失败原因是 openEuler 官方仓库（`repo.openeuler.org`）在 aarch64 架构的 HTTP/2 服务端存在间歇性协议错误，属于 CI 基础设施 / 上游仓库问题，并非 Dockerfile 编写错误。

多个 RPM 包（`git-core`、`gcc-c++`、`guile`）均出现相同类型的 HTTP/2 流错误，且部分包（如 `git-core`）经 dnf 自动重试后成功下载，进一步说明问题出在服务器端而非客户端或 Dockerfile。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试。** 该失败为 openEuler 官方仓库 `repo.openeuler.org` 的 HTTP/2 服务端瞬时协议错误（`INTERNAL_ERROR`），属于临时性基础设施波动。等待仓库服务恢复后重新触发 CI 构建即可，Dockerfile 本身无需任何修改。

### 方向 2（置信度: 低）
**如果该问题持续复现**，可考虑在 Dockerfile 的 `dnf install` 之前添加 `dnf config-manager` 或 `echo` 配置，强制 dnf/curl 降级使用 HTTP/1.1 绕过 HTTP/2 服务端 bug（如设置 `http2=false` 或类似 dnf 配置项）。此方向仅在问题反复出现且确认是仓库 HTTP/2 实现存在持续缺陷时才有必要。

## 需要进一步确认的点
- 该仓库服务器 HTTP/2 流错误是否为临时性波动（重试 CI 即可确认）。
- 若重试多次后相同 aarch64 runner 上仍然失败，需排查 `repo.openeuler.org` 的 CDN 节点是否存在 aarch64 路径特有的 HTTP/2 实现缺陷，或考虑将 aarch64 下载 fallback 到其他镜像站。
