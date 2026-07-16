# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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

Dockerfile:6
   6 | >>> RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all
ERROR: failed to solve: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: aarch64 CI runner 在执行 `dnf install` 时，与 `repo.openeuler.org` 之间的 HTTP/2 连接反复出现 `Stream error in the HTTP/2 framing layer: INTERNAL_ERROR (err 2)`，导致多个 RPM 包（git-core、gcc-c++、guile）下载失败。其中 guile 包在所有镜像源重试后仍下载失败，导致 `dnf install` 以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准的 vvenc Dockerfile（包含 `dnf install`、`git clone`、`cmake` 构建步骤），Dockerfile 本身语法和内容均正确。CI 失败完全由 `repo.openeuler.org` 仓库服务器端的 HTTP/2 协议层错误导致，属于基础设施/网络层面的偶发性问题。这一点可由以下事实佐证：
- 多个不同 RPM 包（git-core、gcc-c++、guile）均遭遇相同的 HTTP/2 stream 错误，而非单个特定包不存在（非 404）
- 部分包（git-core）在重试后下载成功，但 guile 和 gcc-c++ 的重试均告失败
- 日志中没有显示任何与 PR 改动内容相关的编译错误、Dockerfile 语法错误或应用层错误

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 由于失败原因是 `repo.openeuler.org` 仓库服务器端的 HTTP/2 协议层偶发性错误，与 PR 代码无关，最简单的修复方式是重新运行 CI job。大部分情况下，网络波动消除后即可构建成功。若重试后仍然失败，则需进一步排查仓库侧是否存在持续性问题。

### 方向 2（置信度: 低）
若该问题持续复现，可在 Dockerfile 的 `dnf install` 命令前添加 `dnf install` 的重试逻辑，或通过 `dnf` 配置将 HTTP/2 降级为 HTTP/1.1（如 `echo "http2=false" >> /etc/dnf/dnf.conf`），但这属于绕过基础设施问题的临时方案，不建议作为首选修复方向。

## 需要进一步确认的点
- `repo.openeuler.org` 在 aarch64 架构上的 openEuler 24.03-LTS-SP4 仓库是否近期存在 HTTP/2 服务端问题。
- 同期的其他 PR 在 aarch64 runner 上是否也出现类似 HTTP/2 stream 错误（用以确认该问题是单点偶发还是普遍现象）。
- CI runner 节点的 curl/libcurl 版本是否与 repo.openeuler.org 的 HTTP/2 实现存在已知兼容性问题。
