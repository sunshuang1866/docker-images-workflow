# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2错误
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
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在下载大型包（cmake-data 16M、git-core 11M、gcc-c++ 13M）时反复出现 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），dnf 重试多个镜像后耗尽，最终因 gcc-c++ 包下载失败导致整个安装步骤中断。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile` 及配套元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `dnf install` 命令语法正确、包名有效（小包如 acl、autoconf、automake 等均下载成功），失败纯粹因为 openEuler 24.03-LTS-SP4 仓库镜像在下载重型 RPM 包时出现 HTTP/2 协议层错误。这是一个 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 中）
**重新触发 CI 构建**。HTTP/2 流错误（`INTERNAL_ERROR`）通常是仓库镜像侧的临时性问题（如 CDN 节点异常、连接池耗尽），多数情况下重试即可通过。日志中多个包都在不同阶段遇到同类错误但重试后部分成功（cmake-data 在重试后于 #7 1252.9 成功，git-core 在重试后于 #7 1953.8 成功），说明仓库并非完全不可用，仅偶发中断。重新触发后大概率可以通过。

### 方向 2（置信度: 低）
若多次重试仍失败，可能需要联系 openEuler 24.03-LTS-SP4 仓库运维团队排查镜像站 HTTP/2 服务稳定性，或临时将 Dockerfile 中的 dnf repo 指向备用镜像源。

## 需要进一步确认的点
1. 是否有其他使用 `openeuler:24.03-lts-sp4` 基础镜像的 PR 在同一时间段也遇到类似 `dnf install` 下载失败？若有多起案例，说明仓库侧存在问题而非偶发。
2. 重试后是否持续失败？若多次重试（如 3 次以上）仍然在下载 gcc-c++ 时失败，可能需要排查该特定包在镜像站的存储状态。
