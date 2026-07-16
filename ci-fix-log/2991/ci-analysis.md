# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Stream error, INTERNAL_ERROR, No more mirrors to try, repo.openeuler.org

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: openEuler 24.03-LTS-SP4 官方仓库 `repo.openeuler.org` 在 aarch64 runner 上出现 HTTP/2 流错误（Curl error 92），多个包（git-core、gcc-c++、guile）在下载过程中 HTTP/2 连接异常中断。其中 git-core 和 gcc-c++ 重试后成功，但 `guile` 包（git 的依赖）所有重试均失败，耗尽全部镜像后导致 `dnf install` 整体失败。

### 与 PR 变更的关联
**此次失败与 PR 变更无关。** PR 仅新增了一个标准的 Dockerfile，其 `dnf install` 命令格式与项目中大量其他 Dockerfile 完全一致。失败纯粹由 `repo.openeuler.org` 镜像站对外部 aarch64 请求的 HTTP/2 连接不稳定导致，属于 CI 基础设施/上游仓库的瞬时网络问题。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 该失败是上游 openEuler 仓库镜像站的瞬时 HTTP/2 网络问题，不是代码或 Dockerfile 的错误。在仓库服务恢复稳定后重新触发 CI 构建即可通过。不需要修改任何代码。

### 方向 2（置信度: 低，仅当问题持续复现时考虑）
若问题反复出现，可在 Dockerfile 中为 `dnf install` 添加 `--retries 5 --setopt=timeout=30` 等重试参数以增强网络波动容忍能力。但根因在上游仓库而非本地构建逻辑，此为备选方案。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库在 CI 构建时段是否存在服务端 HTTP/2 协议异常（可能与 CDN/反向代理层有关）
- 如果 x86-64 架构的并行构建 job 也失败，可进一步确认是仓库端全架构问题还是仅 aarch64 受影响
