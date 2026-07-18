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
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像在 HTTP/2 下载过程中多次出现流层错误（Curl error 92），其中 `gcc-c++` 包经两次重试后仍然失败，dnf 耗尽所有镜像后报错退出。`cmake-data` 和 `git-core` 同样遇到该错误但重试后成功，表明是仓库镜像端的间歇性网络问题。

### 与 PR 变更的关联
与 PR 变更**无关**。本次 PR 仅新增了一个 Dockerfile 和三项元数据文件（README.md、image-info.yml、meta.yml），均为纯文本/配置变更。失败发生在 `dnf install` 从远端仓库下载 RPM 包阶段，属于 CI 基础设施（仓库镜像服务）的瞬时故障，Dockerfile 中声明的依赖包列表本身无问题。

## 修复方向

### 方向 1（置信度: 高）
向 CI 团队反馈 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）存在间歇性 HTTP/2 流层错误，建议从基础设施侧排查镜像服务器的 HTTP/2 配置或网络稳定性。PR 作者无需修改代码，等待镜像服务恢复后重新触发 CI 构建即可。

## 需要进一步确认的点
- 其他基于 openEuler 24.03-LTS-SP4 的镜像构建是否也在同时段出现相同错误，以确认是否为仓库镜像的普遍性问题而非孤立事件。
- 若问题持续出现，需确认 `repo.****.org` 是否有其他可用的镜像源作为 fallback。
