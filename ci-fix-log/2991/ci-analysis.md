# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: dnf下载HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, dnf install

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
- 失败原因: aarch64 CI runner 从 `repo.openeuler.org` 下载 RPM 包时，HTTP/2 流层反复出现 `INTERNAL_ERROR (err 2)` 错误，导致 `git-core`、`gcc-c++`、`guile` 等多个包下载失败，`guile`（git 的传递依赖）重试耗尽所有镜像后最终失败，`dnf install` 以 exit code 1 退出

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准的 Dockerfile，其中 `dnf install -y git gcc gcc-c++ make cmake` 命令语法正确、包名合法。失败完全是 CI 构建环境与 openEuler RPM 仓库之间的网络问题导致的——HTTP/2 流被服务端异常关闭（`INTERNAL_ERROR`），属于基础设施层面的瞬时故障。

## 修复方向

### 方向 1（置信度: 高）
此失败为 CI 基础设施网络瞬时故障（`repo.openeuler.org` HTTP/2 服务端异常），与 PR 代码无关。**直接重新触发 CI 构建**即可，网络恢复后 `dnf install` 应能正常完成。

### 方向 2（置信度: 低，兜底方案）
若多次重试后该问题持续出现，可考虑在 Dockerfile 中为 `dnf` 添加重试参数（如 `--setopt=retries=10`），或在 `dnf install` 前先执行一次 `dnf makecache` 预缓存元数据以减少单次请求压力。但这属于绕行方案，根因仍在上游镜像站。

## 需要进一步确认的点
- 检查 `repo.openeuler.org` 在 CI 构建时段（2026-07-09 14:09 UTC）的服务状态，确认是否发生过 HTTP/2 服务端异常或镜像同步问题
- 确认同一时段其他使用 `openEuler-24.03-LTS-SP4` 仓库的 job 是否也出现类似下载失败，以判断故障范围
