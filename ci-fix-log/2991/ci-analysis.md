# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2协议错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 1709.7   guile-5:2.2.7-6.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`:6（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: openEuler 24.03-LTS-SP4 官方仓库（`repo.openeuler.org`）在 aarch64 CI runner 上返回 HTTP/2 INTERNAL_ERROR，导致多个 aarch64 RPM 包（`git-core`、`gcc-c++`、`guile`）下载中断。其中 `guile` 包耗尽所有镜像重试后彻底失败，`dnf install` 以 exit code 1 退出。这是仓库服务器的 HTTP/2 协议层故障，与 PR 代码变更无关。

### 与 PR 变更的关联
**无关联。** PR 仅新增了 vvenc 1.14.0 在 openEuler 24.03-lts-sp4 上的 Dockerfile、README.md 条目、image-info.yml 条目和 meta.yml 条目。Dockerfile 内容正确，`dnf install` 命令语法无误。失败完全由 `repo.openeuler.org` 仓库镜像在 aarch64 架构上的 HTTP/2 服务端错误导致。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重试 CI 构建即可。** 该失败为 openEuler 官方仓库 `repo.openeuler.org` 在 aarch64 上的 HTTP/2 服务端瞬时故障（stream INTERNAL_ERROR），属基础设施问题。待仓库服务恢复后重新触发 CI 构建即可通过。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 aarch64 仓库 HTTP/2 服务在重试时已恢复正常
- 如果多次重试后该问题持续出现，需联系 openEuler 基础设施团队排查 `repo.openeuler.org` 的 HTTP/2 层配置
