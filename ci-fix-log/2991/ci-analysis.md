# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf, repo.openeuler.org, aarch64

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
- 失败原因: 在 aarch64 架构 runner 上执行 `dnf install -y git gcc gcc-c++ make cmake` 时，`repo.openeuler.org` 仓库服务器多次返回 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），导致 `git-core`、`gcc-c++`、`guile` 三个包的下载失败。其中 `guile` 在耗尽所有镜像重试后仍未成功，dnf 最终以 exit code 1 失败。这是 CI 基础设施/仓库服务端问题，与 PR 代码变更无关。

### 与 PR 变更的关联
PR 仅新增了 `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile` 及其元数据文件（README.md、doc/image-info.yml、meta.yml）。新增的 Dockerfile 中 `dnf install -y git gcc gcc-c++ make cmake` 命令语法完全正确，所有包名均有效（日志显示 dnf 成功解析依赖并开始下载 156 个包，部分包已成功下载）。失败完全由 openEuler 仓库服务器端 HTTP/2 协议错误所致，与 PR 变更无任何因果关系。

## 修复方向

### 方向 1（置信度: 高）
这是一个基础设施层面的网络问题，不是代码问题。无需修改任何 Dockerfile 或元数据文件。应通过以下方式处理：
- 等待仓库 `repo.openeuler.org` 的 aarch64 节点恢复后重新触发 CI 构建
- 或在 CI 触发时手动重试（retry），同样的构建命令在仓库服务正常时应当通过

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 aarch64 仓库节点在当前时间段是否存在已知的 HTTP/2 服务不稳定问题
- 确认其他同时段的 aarch64 CI job 是否也出现相同的 `Curl error (92)` 错误，以排除 runner 本地网络问题
