# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 包仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install, repo.openeuler.org, aarch64

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

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: 在 aarch64 runner 上执行 `dnf install -y git gcc gcc-c++ make cmake` 时，`repo.openeuler.org` 的 HTTP/2 传输层出现间歇性流错误（Curl error 92），导致 `guile`（git 的传递依赖）等 RPM 包下载失败。`dnf` 的重试机制耗尽了所有镜像后仍无法完成下载，构建失败。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了标准格式的 Dockerfile（使用 `dnf install` 安装 `git gcc gcc-c++ make cmake`）和配套的文档/元数据更新。失败原因是 `repo.openeuler.org` aarch64 仓库的 HTTP/2 传输层不稳定，属于 CI 基础设施/上游仓库侧的网络问题。日志显示多个 aarch64 包的下载均遭遇了相同的 HTTP/2 流错误，部分包通过重试成功（如 `git-core`），但 `guile` 最终因所有镜像重试耗尽而失败。

## 修复方向

### 方向 1（置信度: 高）
**无需修复 PR 代码**。这是一个 transient（瞬时性）基础设施错误——`repo.openeuler.org` 的 aarch64 仓库 HTTP/2 传输层不稳定。处理方式：
- **重试 CI**：在非高峰期重新触发 CI 构建，大概率可以通过（其他 155 个包中的大多数已成功下载，仅 `guile` 最终耗尽重试）。
- 若多次重试仍失败，向 openEuler 基础设施团队报告 `repo.openeuler.org` aarch64 仓库的 HTTP/2 流稳定性问题。

## 需要进一步确认的点
无。日志证据充分，根因明确为 `Curl error (92): Stream error in the HTTP/2 framing layer` 导致的包下载失败，属于基础设施层面问题，与 PR 代码变更无关联。
