# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM 仓库 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: CI 构建环境在通过 DNF 从 `repo.****.org`（openEuler 官方仓库镜像）下载 RPM 包时，curl 报告 HTTP/2 流错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），导致 `gcc` 等核心包下载失败，DNF 重试所有镜像后仍无法完成下载，Docker 构建失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR #2992 的改动仅为新增 multiwfn 的 SP4 版本 Dockerfile 及相应文档/元数据条目（README.md、image-info.yml、meta.yml），Dockerfile 中的 `dnf install` 命令语法正确、包名合法。失败的直接原因是 openEuler 24.03-LTS-SP4 软件仓库在构建时刻出现 HTTP/2 传输层异常，属于 CI 基础设施侧的 transient 网络问题，不涉及 PR 代码缺陷。

## 修复方向

### 方向 1（置信度: 高）
**等待仓库恢复后重试构建。** 此失败为 openEuler 24.03-LTS-SP4 RPM 镜像站的 HTTP/2 服务端临时故障（stream closed with INTERNAL_ERROR），与 PR 代码无关。Code Fixer 无需修改任何代码，触发 CI re-run 即可。如果重建后仍失败，需由基础设施团队排查 `repo.****.org` 的 HTTP/2 协议栈是否与 curl 客户端存在兼容性问题。

## 需要进一步确认的点
- 确认 `repo.****.org`（即 openEuler 24.03-LTS-SP4 软件包仓库）在构建时段的可用性状态
- 同一时段是否有其他 PR 的 24.03-LTS-SP4 构建也遭遇相同 Curl error (92) — 若存在，可确认为仓库侧问题
- 确认 CI runner 使用的 curl/libcurl 版本是否与仓库的 HTTP/2 实现存在已知兼容性问题
