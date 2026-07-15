# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM镜像站HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), repo.openeuler.org, dnf install

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
- 失败原因: CI 在 aarch64 runner 上执行 `dnf install` 时，从 `repo.openeuler.org` 下载 RPM 包（git-core、gcc-c++、guile）遭遇多次 HTTP/2 流错误（Curl error 92），DNF 重试所有可用镜像后仍无法成功下载 `guile-2.2.7-6.oe2403sp4.aarch64.rpm`，导致依赖安装失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准的 Dockerfile（安装基础构建依赖 → clone vvenc → cmake 构建），Dockerfile 内 `dnf install -y git gcc gcc-c++ make cmake` 命令本身完全正确。失败原因是 openEuler 官方 RPM 镜像站 `repo.openeuler.org` 在处理 aarch64 架构的 HTTP/2 请求时，多个 RPM 包下载流被服务端异常关闭（`INTERNAL_ERROR`），属于 CI 基础设施/上游服务问题。在 156 个待安装包中，大多数包下载成功（如 cmake、gcc、binutils、cpp 等），仅 git-core、gcc-c++、guile 这 3 个包反复遭遇 HTTP/2 流错误，表明这是间歇性网络协议层问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 Dockerfile，重试构建即可。** 这是 `repo.openeuler.org` 镜像站在该时间点的临时 HTTP/2 服务端异常，与 PR 代码无关。等待镜像站恢复或直接触发 CI 重新构建，有很大概率可以成功通过。

### 方向 2（置信度: 低）
在 dnf 配置中禁用 HTTP/2（设置 `http2=false`），降级到 HTTP/1.1 协议绕过 HTTP/2 流错误。但这属于基础设施层面的配置调整，且本次失败的 HTTP/2 错误可能是临时性的，不建议仅为规避临时问题而修改构建流程。

## 需要进一步确认的点
- `repo.openeuler.org` 的 HTTP/2 服务端是否存在已知问题或正在维护中
- 其他使用 `repo.openeuler.org` 作 RPM 源的 aarch64 构建是否也同期出现类似 HTTP/2 流错误
