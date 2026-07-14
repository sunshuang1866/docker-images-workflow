# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install, gcc-c++

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像（`repo.****.org`）在 HTTP/2 传输层发生多次流错误（Curl error 92: Stream error in the HTTP/2 framing layer），导致 `gcc-c++` 等 RPM 包下载失败。dnf 尝试了所有可用镜像均未成功，最终退出码为 1。这是 CI 基础设施/网络层面的问题，与 PR 代码变更无关。

### 与 PR 变更的关联
**无关。** PR #2980 的变更仅新增了一个 grADS 2.2.3 的 Dockerfile 及配套的 README、image-info.yml、meta.yml 条目。`dnf install` 命令中列出的包名均为 openEuler 标准仓库中存在的合法包，Dockerfile 语法正确。失败根因是 openEuler 24.03-LTS-SP4 的软件仓库镜像端发生了 HTTP/2 传输层异常，导致部分 RPM 包（尤其是 `gcc-c++-12.3.1-110.oe2403sp4`）无法下载。同样的 `dnf install` 列表若在其他时段/网络重试可能正常通过。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 CI 基础设施的临时性网络故障（repo 镜像 HTTP/2 流传输异常），建议触发 CI 重试（re-run）。如果仓库镜像持续不可用，需要运维侧排查 `repo.****.org` 的反向代理/CDN 的 HTTP/2 配置是否存在问题。

## 需要进一步确认的点
1. 同一时段内其他 24.03-lts-sp4 的镜像构建是否也失败（确认是仓库侧故障而非本 PR 特有）？
2. `repo.****.org` 服务端的 HTTP/2 实现是否存在已知缺陷（如某些 CDN/代理对 HTTP/2 流的处理不稳定）？
3. 重试后是否可以成功拉取 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm`？
