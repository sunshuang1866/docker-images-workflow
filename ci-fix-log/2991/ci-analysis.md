# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF包下载HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, repo.openeuler.org

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
```
```
Dockerfile:6
--------------------
   6 | >>> RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all
--------------------
ERROR: failed to solve: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: CI aarch64 runner 在执行 `dnf install` 时，从 `repo.openeuler.org` 下载 3 个 RPM 包（`git-core`、`gcc-c++`、`guile`）均遇到 HTTP/2 流传输协议错误（Curl error 92），导致 `guile` 包最终耗尽所有镜像重试次数而安装失败。这是 openEuler 仓库服务器端的临时 HTTP/2 协议异常或 CI 构建环境与仓库之间的网络不稳定所致，与 PR 代码变更无关。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 语法和逻辑均正确：`BASE=openeuler/openeuler:24.03-lts-sp4` 基础镜像拉取成功，`dnf install -y git gcc gcc-c++ make cmake` 命令本身正确。失败发生在 dnf 下载 RPM 包的纯网络层面——仓库服务器返回 HTTP/2 流错误（`INTERNAL_ERROR`），这是服务端/网络基础设施问题。其他已存在的 sp3 Dockerfile 使用相同的 `dnf install` 模式且正常运行，进一步证明失败与 PR 代码无关。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试。** 这是临时性网络/仓库基础设施故障。`Curl error (92): HTTP/2 stream was not closed cleanly: INTERNAL_ERROR` 是上游仓库服务器端的间歇性 HTTP/2 协议问题，通常在重新构建时自动恢复。无需修改任何代码，直接 re-run 该 CI job 即可。

### 方向 2（置信度: 低）
如果多次重试均以相同方式失败，则可能是 openEuler 24.03-LTS-SP4 仓库的 `OS/aarch64` 源存在持续性 HTTP/2 配置问题。此时需要在 Dockerfile 中通过设置 dnf 配置或 curl 参数尝试降级到 HTTP/1.1（如 `echo 'http2=false' >> /etc/dnf/dnf.conf` 或设置 `libcurl` 相关环境变量），但这仅为低优先级的备用推测，当前证据不支撑此结论。

## 需要进一步确认的点
- 由于日志已明确显示为网络层面的 infra-error，证据充足，无需额外确认。建议 re-run 后观察是否通过即可。

## 修复验证要求
无需修复。此失败为网络基础设施问题，Code Fixer 无需处理任何代码变更。若 re-run 后仍失败，需获取该时间点 `repo.openeuler.org` 的 aarch64 仓库服务状态确认。
