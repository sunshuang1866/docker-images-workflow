# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, repo.****.org

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`RUN dnf install -y git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel`）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像 `repo.****.org` 在 CI 构建期间出现 HTTP/2 流层协议错误（curl error 92: INTERNAL_ERROR），导致多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）下载失败。经过多次镜像重试后，`gcc` 包耗尽所有可用镜像，`dnf install` 最终报错退出。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 multiwfn 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及相关元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 语法和包名均正确。失败根因是 CI 构建时 openEuler 24.03-LTS-SP4 官方 RPM 仓库的 HTTP/2 服务端临时故障，属于基础设施层面的网络问题。同一仓库的 stage-1（运行时阶段）也遇到了相同的 curl error 92。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码。** 这是 CI 基础设施/上游仓库的临时网络故障。应触发 CI 重试（re-run），等待 openEuler 24.03-LTS-SP4 的 RPM 仓库镜像恢复正常即可通过。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 的 `repo.****.org` 仓库在 CI 重试时是否稳定可用。
- 如果多次重试仍然失败，需检查该仓库地址是否发生变更或存在持续性网络连通问题。

