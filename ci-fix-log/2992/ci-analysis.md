# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（`RUN dnf install -y` 步骤，builder 阶段）
- 失败原因: openEuler 24.03-LTS-SP4 RPM 仓库（`repo.****.org`）的 HTTP/2 服务端反复出现 `INTERNAL_ERROR` 导致连接流被非正常关闭（Curl error 92），多个大型 RPM 包（gcc 34MB、gcc-gfortran 13MB、guile 6.3MB）下载过程中数次重试均失败，dnf 耗尽所有镜像源后放弃。

### 与 PR 变更的关联
**与 PR 无关。** 本次 PR 仅新增了 multiwfn 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套的 README、image-info.yml、meta.yml 条目。Dockerfile 中 `dnf install` 的写法与同目录下已有 SP3 版本完全一致。失败原因是 dnf 在从 openEuler 官方仓库下载 RPM 包时遇到 HTTP/2 协议层面的服务端错误，属于 CI 基础设施/仓库服务器问题，不是代码缺陷。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码，触发重新构建即可。** 该失败是 openEuler RPM 仓库 HTTP/2 服务的临时性故障导致的下载中断（多个 stream 的 `INTERNAL_ERROR`）。如果重试后仍失败，需联系 openEuler 仓库运维排查服务端 HTTP/2 配置。

### 方向 2（置信度: 低）
若问题持续复现，可尝试在 Dockerfile 中为 dnf 配置 HTTP/1.1 回退（`echo "http2=false" >> /etc/dnf/dnf.conf` 或类似手段），绕过 HTTP/2 层的问题。但这是绕过方案而非根因修复，不推荐作为首选。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 RPM 仓库（`repo.****.org`，实际为 `repo.openeuler.org`）在 CI 构建时段的 HTTP/2 服务状态是否正常
- 确认相同仓库在其他 PR 的 SP4 构建中是否也出现相同错误（判断是系统性故障还是偶发）
- 构建日志中 `#7`（stage-1，32 个包）和 `#8`（builder，157 个包）都出现了同类错误，但 `#7` 进度更快且未先失败——这说明仓库服务器在大批量并发下载时更容易触发 HTTP/2 流错误
