# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP/2传输错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段 `RUN dnf install` 步骤）
- 失败原因: CI 构建环境在通过 dnf 从 openEuler 24.03-LTS-SP4 仓库镜像下载 RPM 包时，遇到 HTTP/2 传输层协议错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），多个包（gcc-gfortran、glibc-devel、guile、gcc）反复重试后仍失败，最终 `gcc` 包耗尽所有镜像重试次数，dnf 安装失败退出。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了一个 Dockerfile（`Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`）和 3 个元数据文件的修改（README.md、image-info.yml、meta.yml），均为常规文档和构建描述性变更。失败的直接原因是 openEuler 24.03-LTS-SP4 软件仓库镜像的 HTTP/2 服务端问题，属于 CI 基础设施层面的问题。Dockerfile 本身的 `dnf install` 指令语法和包名均正确，同日同仓库的 SP3 版本构建正常也从侧面印证了这一点。

## 修复方向

### 方向 1（置信度: 高）
**重试触发 CI 重新构建。** 该失败为 openEuler 24.03-LTS-SP4 软件仓库镜像的临时性网络/服务端问题，大概率可通过重新触发 CI 构建解决。建议等待仓库镜像服务恢复后重新运行 CI，或在仓库稳定时段重试。

### 方向 2（置信度: 低）
如果重新触发后仍持续失败，需排查：① openEuler 24.03-LTS-SP4 的 repo 源 URL 是否已变更；② CI 构建节点到 repo 镜像的网络连通性是否正常；③ DNS 解析是否指向了有问题的镜像节点。

## 需要进一步确认的点
1. openEuler 24.03-LTS-SP4 的 OS 仓库镜像（`repo.****.org`）在 CI 构建时段（2026-07-09 14:46 UTC）是否存在已知的服务中断或 HTTP/2 协议兼容性问题。
2. 同一个 CI runner（`ecs-build-docker-x86-03-sp`）在相近时段内其他 openEuler 24.03-lts-sp4 镜像构建是否也出现同类错误，以确认是个别镜像问题还是全局性问题。
