# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
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
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: Dockerfile:6（`RUN dnf install -y ...` 步骤）
- 失败原因: 构建过程中 `dnf install` 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时，多个包（`cmake-data`、`git-core`、`gcc-c++`）遭遇 HTTP/2 协议层流错误（Curl error 92: INTERNAL_ERROR），其中 `gcc-c++` 在两次重试后耗尽所有镜像源仍未能成功下载，导致整个 `dnf install` 命令失败。该问题与 PR 代码变更无关，属于仓库服务器 HTTP/2 服务端的瞬时或协议兼容性问题。

### 与 PR 变更的关联
**本次 PR 的故障为 infra-error，与 PR 代码变更无关。**

PR #2980 新增了 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`（30 行）及相关元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 内容完全正常：基础镜像、`dnf install` 命令、源码构建步骤均无语法或逻辑错误。构建失败发生在 Docker 构建的第二步（`dnf install`），原因是 openEuler 24.03-LTS-SP4 软件仓库服务器在对 `gcc-c++` 等大包进行 HTTP/2 传输时持续返回 INTERNAL_ERROR 流错误，与 Dockerfile 内容、PR 改动无关。

日志中 `cmake-data` 和 `git-core` 也出现了同类错误但通过重试其他镜像成功下载，说明该问题是服务端 HTTP/2 实现的间歇性缺陷，仅在特定包（如 13MB 的 `gcc-c++`）的重试中全部失败。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复，建议重跑 CI。**

这是一个 CI 基础设施/上游仓库问题。openEuler 仓库镜像站的 HTTP/2 服务在传输大文件（`gcc-c++` 约 13MB）时出现流中断。问题具有间歇性特征：`cmake-data` 和 `git-core` 通过重试其他镜像成功下载。`gcc-c++` 的两次重试恰好都抽到了有问题的镜像。建议：
1. 直接触发 CI 重跑（retry），大概率能通过
2. 如持续失败，联系 openEuler 24.03-LTS-SP4 仓库管理员排查 HTTP/2 反向代理/负载均衡配置

### 方向 2（置信度: 低）
**作为规避手段，在 Dockerfile 的 `dnf install` 前禁用 HTTP/2。**

如果重跑持续失败且无法等待上游修复，可在 Dockerfile 中添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 或在 BuildKit 层面配置 HTTP/1.1。但这属于临时规避，不应作为首选方案。

## 需要进一步确认的点
- 日志已足以确定根因，无需额外确认。仓库 `repo.****.org` 的 HTTP/2 实现存在间歇性问题，该问题是故障的唯一原因。
