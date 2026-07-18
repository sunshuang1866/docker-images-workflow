# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库下载HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: 在 aarch64 runner 上，`dnf install` 从 `repo.openeuler.org` 下载 RPM 包时，多个包（git-core、gcc-c++、guile）遭遇 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），其中 `guile` 包在耗尽所有镜像重试后仍未下载成功，导致 dnf 安装失败退出码 1。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 仅新增了一个标准的 vvenc Dockerfile（安装 gcc/gcc-c++/cmake/make 后编译 vvenc），Dockerfile 中的 `dnf install` 命令语法正确、包名正确。失败原因是构建时 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库出现 HTTP/2 传输层间歇性错误，属于 CI 基础设施/上游仓库的临时网络问题。

## 修复方向

### 方向 1（置信度: 高）
**CI 基础设施问题，无需修改代码。** 该失败是 `repo.openeuler.org` 仓库在构建时段的 HTTP/2 传输层不稳定导致的临时性故障。直接重新触发 CI 构建即可——仓库恢复后 dnf 安装应能正常完成。建议在重试前确认 `repo.openeuler.org` 的 aarch64 仓库可访问性。

## 需要进一步确认的点
- `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库在构建时段是否存在已知的服务端 HTTP/2 问题
- 同一个 PR 的 x86_64 (amd64) 架构构建是否也失败，还是仅 aarch64 受影响（日志中显示运行在 `ecs-build-docker-aarch64-04-sp` 节点上）

## 修复验证要求
无需代码修复，无需验证。重新触发 CI 后确认构建通过即可。
