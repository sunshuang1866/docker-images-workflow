# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, dnf

## 根因分析

### 直接错误
```
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `dnf install` 步骤）
- 失败原因: CI 构建环境（x86_64 runner `ecs-build-docker-x86-03-sp`）与 openEuler 24.03-LTS-SP4 仓库镜像站之间的 HTTP/2 传输层发生协议错误（Curl error 92：`INTERNAL_ERROR`），多个大型 RPM 包（gcc-gfortran 13MB、guile 6.3MB、gcc 34MB）下载重试耗尽所有 mirror 后失败。

### 与 PR 变更的关联
与 PR 变更**无直接关联**。PR 仅新增了 multiwfn 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 结构本身与已有的 24.03-LTS-SP3 版本一致，无语法或逻辑错误。构建过程中 `dnf install` 的 package 列表均为 openEuler 24.03-LTS-SP4 仓库中存在的标准包，失败纯粹由仓库镜像站的 HTTP/2 传输异常导致。

此外，`#7`（stage-1 阶段镜像，安装 32 个包）也遭遇了多次 Curl error 92，进一步确认这是一次系统性的网络基础设施故障，而非特定包或 Dockerfile 的问题。

## 修复方向

### 方向 1（置信度: 中）
**重试构建**。HTTP/2 `INTERNAL_ERROR` 通常是仓库服务器端的瞬时故障或网络链路抖动。等待仓库镜像站恢复后重新触发 CI 构建即可通过，无需修改任何代码。若同类错误频繁出现，需由 CI 基础设施团队排查 runner 与 openEuler 仓库之间的网络链路或 HTTP/2 代理配置。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 的 `repo.****.org` 镜像站在 CI 构建时段是否存在服务不稳定或 HTTP/2 协议兼容性问题。
- 其他 PR 在同时间段是否也出现类似的 `Curl error (92)` 错误，以确认是否为仓库侧的普遍故障。
