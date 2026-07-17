# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-16`
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像（`repo.****.org`）在下载 RPM 包时多次出现 HTTP/2 流错误（Curl error 92: `HTTP/2 stream was not closed cleanly: INTERNAL_ERROR`），涉及 `cmake-data`、`git-core`、`gcc-c++` 三个包。DNF 在重试所有可用镜像后，`gcc-c++` 包仍无法下载成功，导致 `dnf install` 整体失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR #2980 仅新增了一个标准格式的 Dockerfile（引用 `openeuler/openeuler:24.03-lts-sp4` 基础镜像并使用 `dnf install` 安装依赖）、更新了 README、image-info.yml 和 meta.yml。`dnf install` 命令本身格式正确，失败完全由 openEuler 24.03-LTS-SP4 仓库镜像端 HTTP/2 协议层面的网络问题导致，属于 CI 基础设施故障。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 openEuler 24.03-LTS-SP4 软件仓库镜像（`repo.****.org`）的 HTTP/2 服务端问题导致的临时性网络故障。Code Fixer 无需对 PR 代码做任何修改。建议操作：等待镜像站恢复后重新触发 CI 构建（retry），或在 CI 环境中为 DNF 配置 `http2=false` 降级为 HTTP/1.1 规避此类问题。

## 需要进一步确认的点
- 确认 `repo.****.org` 的 HTTP/2 服务是否已恢复稳定（联系运维或镜像站管理员）。
- 确认同一时间段内其他 openEuler 24.03-LTS-SP4 镜像构建是否也出现相同错误（以确认是否为单点故障）。
- 如果此类问题频繁出现，可考虑在 CI 环境中配置 DNF 的 `http2=false` 或在 Dockerfile 中为 `dnf` 命令添加重试机制（如 `--setopt=retries=10`）。
