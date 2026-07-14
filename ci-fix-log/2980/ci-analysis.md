# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error, HTTP/2 framing layer, No more mirrors to try, dnf install

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
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-16`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 软件仓库（`repo.****.org`）在下载 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 时反复出现 HTTP/2 流层错误（Curl error 92: INTERNAL_ERROR），所有镜像源均尝试失败，导致 `dnf install` 命令退出码为 1。

### 与 PR 变更的关联
**与 PR 无关**。这是一个 CI 基础设施/网络问题。PR 仅新增了一个 Dockerfile 及配套的元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 中 `dnf install` 的包列表语法正确、包名有效——日志中 `Dependencies resolved` 确认了依赖解析成功（258 个包，总计 914 MB）。问题出在下载阶段：仓库镜像服务器返回了 HTTP/2 协议层内部错误。值得注意的是，同一次构建中 `cmake-data` 和 `git-core` 也触发了同样的 Curl error (92)，但它们通过重试最终下载成功；`gcc-c++`（13 MB）在两次重试后耗尽了所有镜像源。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 CI 构建时 RPM 仓库的临时网络故障（HTTP/2 协议层内部错误），与 PR 的代码变更无关。建议直接**重试 CI**（在 Jenkins 中重新触发构建）。如果仓库镜像持续不稳定，可考虑在 Dockerfile 的 `dnf install` 前添加重试机制（如 `dnf install -y --setopt=retries=10 ...`），但通常一次重试即可成功。

## 需要进一步确认的点
- 确认 `repo.****.org`（openEuler 24.03-LTS-SP4 仓库镜像）当时的服务状态是否正常。
- 如果多次重试仍失败，需检查仓库镜像是否有 HTTP/2 配置问题，或考虑在 CI 构建环境中禁用 HTTP/2（设置 curl 的 `--http1.1` 或环境变量 `CURL_HTTP_VERSION=1.1`）。
