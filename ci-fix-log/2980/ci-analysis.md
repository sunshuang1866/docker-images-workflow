# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 镜像源HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像源出现间歇性 HTTP/2 流错误（Curl error 92），导致 `gcc-c++` 等大型 RPM 包（13 MB）在多次重试后仍下载失败。较小的包（如 cmake-data、git-core）虽然也遇到了同样的 HTTP/2 错误，但重试后成功下载。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 新增的 Dockerfile 中 `dnf install` 包列表是标准且正确的，所有包名均可在 openEuler 24.03-LTS-SP4 仓库中找到（日志中"Transaction Summary"已列出全部 258 个待安装包及其版本信息）。失败纯粹由 `repo.****.org` 镜像站的 HTTP/2 协议层传输异常引起，属于 CI 基础设施问题。其他同样依赖 openEuler 24.03-LTS-SP4 镜像源的 PR 也可能遇到相同问题。

## 修复方向

### 方向 1（置信度: 低）
重试 CI。HTTP/2 流错误属于网络层面的间歇性故障，与代码无关。openEuler 仓库镜像源可能在特定时段不稳定，重新触发 CI 构建大概率可以成功（日志中 cmake-data 和 git-core 均通过重试成功下载，仅 gcc-c++ 的重试次数耗尽）。

### 方向 2（置信度: 低）
在 Dockerfile 的 `dnf install` 命令前添加重试机制（如 `dnf install --setopt=retries=10 --setopt=timeout=120 ...`），增加 dnf 对单个包的下载重试次数，以对抗 HTTP/2 流抖动。但这属于对 CI 基础设施问题的非根本性绕过方案，不推荐作为主修复方向。

## 需要进一步确认的点
1. `repo.****.org` 镜像站的 HTTP/2 协议支持是否存在已知的稳定性问题（如 HTTP/2 流限速、连接复用冲突等）。
2. 同一时段是否有其他使用 openEuler 24.03-LTS-SP4 基础镜像的 CI job 也出现类似 Curl error (92) 失败。
3. CI 构建环境的 Docker BuildKit 和基础镜像中的 `libcurl` 版本是否需要更新以修复 HTTP/2 相关的已知 bug。
4. 观察该 PR 在后续 CI 重试中是否能成功通过——若能，则进一步确认为间歇性网络问题。
