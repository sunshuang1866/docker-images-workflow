# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, dnf install, repo.openeuler.org, aarch64, No more mirrors to try

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
- 失败原因: CI 的 aarch64 构建节点在执行 `dnf install` 从 `repo.openeuler.org` 下载 RPM 包时，多个包（`git-core`、`gcc-c++`、`guile`）遭遇 HTTP/2 流层错误（Curl error 92: INTERNAL_ERROR），`guile` 包在所有镜像重试耗尽后最终下载失败，导致 dnf 安装步骤整体退出码为 1。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 仅新增了一个标准的 vvenc Dockerfile（安装依赖 → git clone → cmake 构建 → cmake 安装），Dockerfile 内容本身没有问题。失败完全由 `repo.openeuler.org` 的 aarch64 RPM 仓库在构建时刻的 HTTP/2 网络传输不稳定导致，属于 CI 基础设施层面的偶发性网络问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码。** 这是 CI 基础设施的临时网络问题（`repo.openeuler.org` 的 HTTP/2 连接不稳定）。建议：
- 重新触发 CI 构建（retry），大部分情况下网络恢复后即可通过。
- 如果反复出现，可考虑在 Dockerfile 的 `dnf install` 命令中添加 `--retries` 参数（如 `dnf install --setopt=retries=10 ...`）以增加网络容错。

## 需要进一步确认的点
- 同时间段内该 CI runner 节点上其他 PR 的 aarch64 构建是否也出现同类 `Curl error (92)` 报错——如果是，则可确认为仓库服务端或节点网络层面的临时故障。
- `repo.openeuler.org` 在构建时刻是否存在服务端 HTTP/2 协议实现的已知问题。
