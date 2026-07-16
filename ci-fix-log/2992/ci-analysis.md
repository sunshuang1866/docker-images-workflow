# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2协议错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, HTTP/2 stream, INTERNAL_ERROR, dnf install, No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `dnf install` 指令）
- 失败原因: openEuler 24.03-LTS-SP4 官方 RPM 仓库（`repo.****.org`）在 CI 构建时发生 HTTP/2 协议层错误，curl 报 `Stream error in the HTTP/2 framing layer: INTERNAL_ERROR (err 2)`，导致 builder 阶段需要下载的 157 个 RPM 包中多个包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）下载失败。dnf 重试全部镜像后仍无法下载 `gcc` 包，最终构建终止（exit code 1）。运行时阶段（#7，32 个包）也出现了同类 HTTP/2 错误（`glibc-devel`、`gcc-gfortran`），但通过重试成功恢复，后因 builder 阶段失败被 CANCELED。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了 openEuler 24.03-LTS-SP4 的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 内容与已有的 sp3 版本在结构和包依赖上完全一致（仅基础镜像 tag 从 `24.03-lts-sp3` 变为 `24.03-lts-sp4`）。失败发生在 `dnf install` 从 openEuler SP4 官方仓库下载 RPM 包的过程中，属于仓库服务器侧 HTTP/2 协议层异常，是典型的 CI 基础设施问题（transient infra error）。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 该错误为 openEuler 24.03-LTS-SP4 官方 RPM 仓库的 transient HTTP/2 协议层故障，与 Dockerfile 内容和 PR 变更无关。直接 re-run CI job 即可。此类 HTTP/2 Stream INTERNAL_ERROR 通常是服务器端或中间代理/LB 的间歇性问题，短时间内重试大概率会成功。

### 方向 2（可选；置信度: 低）
**若重试仍持续失败**，需排查 openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）的 HTTP/2 配置是否存在持久性问题（如 LB 或反向代理的 HTTP/2 流管理 bug），由仓库运维团队处理，不属于 Dockerfile 层面的修复范围。

## 需要进一步确认的点
- 该 CI 失败是否在多次重试后仍然复现？若持续复现，需联系 openEuler 仓库运维确认 SP4 仓库 HTTP/2 服务状态。
- 日志中仓库域名被脱敏为 `repo.****.org`，无法确认具体是哪个 openEuler 镜像站。若重试仍失败，可在 Dockerfile 中将 dnf repo 显式指定为备选镜像站（如 `repo.huaweicloud.com`）来绕过问题仓库。
