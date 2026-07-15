# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success

#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件包仓库镜像（`repo.****.org`）在下载 `gcc-c++` RPM 包时出现 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），`cmake-data` 和 `git-core` 也同样遇到此问题但重试后成功下载，而 `gcc-c++` 在两个不同 HTTP/2 流上均失败，最终耗尽所有镜像后 `dnf` 放弃。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了 grads 2.2.3 在 openEuler 24.03-lts-sp4 上的 Dockerfile（30 行）和元数据文件，Dockerfile 中 `dnf install` 的包列表正确、语法无误。失败根因是 openEuler 24.03-LTS-SP4 仓库镜像服务器端 HTTP/2 连接不稳定（`INTERNAL_ERROR`），属于 CI 基础设施/网络问题，不是 Dockerfile 或 PR 改动导致的。

## 修复方向

### 方向 1（置信度: 高）
无需修改代码。CI 构建基础设施中 openEuler 24.03-LTS-SP4 的 RPM 仓库镜像源存在 HTTP/2 服务端问题，导致大文件（如 13MB 的 `gcc-c++`）下载过程中流被异常关闭。建议：
- 等待仓库镜像服务恢复后重新触发 CI 构建（retry）
- 或在 CI 环境中为 `dnf` 配置 `http2=false` 回避 HTTP/2 问题，改用 HTTP/1.1 下载

## 需要进一步确认的点
- 确认 `repo.****.org` 镜像站的 HTTP/2 服务状态是否已恢复
- 确认该镜像站是否对下载速率或并发连接数有限制

## 修复验证要求
不适用（infra-error，无需代码修复）。重新触发构建即可验证。
