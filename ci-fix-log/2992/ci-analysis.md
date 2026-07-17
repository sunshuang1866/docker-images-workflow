# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: "仓库 HTTP/2 流错误"
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`
- 失败原因: openEuler 24.03-LTS-SP4 软件包仓库（`repo.****.org`）在 Docker 构建期间 HTTP/2 传输不稳定，多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）下载时遭遇 HTTP/2 流中断（Curl error 92: INTERNAL_ERROR），其中 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 在所有镜像站重试后仍无法下载，导致 dnf install 失败（exit code: 1）。

### 与 PR 变更的关联
本次 PR 变更与 CI 失败**无直接关联**。PR 仅新增了 multiwfn 的 openEuler 24.03-LTS-SP4 版本 Dockerfile 及配套文档条目，Dockerfile 中的 `dnf install` 命令格式和包名与已有的 sp3 版本一致，不存在语法或逻辑错误。失败纯粹由构建时 openEuler 软件包仓库的 HTTP/2 服务端异常引起，属于网络基础设施层面的临时故障。日志中同时构建的 stage-1 阶段（`#7`）也出现了相同的 HTTP/2 流错误（`glibc-devel`、`gcc-gfortran`），进一步证实问题出在仓库服务器端而非 Dockerfile 配置。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 该失败为 `infra-error`，由 openEuler 24.03-LTS-SP4 软件包仓库的 HTTP/2 服务端不稳定导致。建议重新触发 CI 构建（retry/rerun），待仓库服务恢复正常后构建应能通过。

### 方向 2（置信度: 低，仅当方向 1 反复失败时考虑）
若多次重试后同一仓库持续出现 HTTP/2 错误，可尝试在 Dockerfile 的 dnf 命令中添加 `--setopt=retries=10 --setopt=timeout=120` 增加重试次数和超时时间，或配置 `deltarpm=0` 和 `fastestmirror=1` 以改善镜像选择。但此类修改属于绕过基础设施问题，不是根本解决方案。

## 需要进一步确认的点
- 该仓库 `repo.****.org` 的 HTTP/2 服务状态是否在 CI 执行时段存在已知故障或维护窗口。
- 同一时段其他 PR 构建同版本基础镜像（`openeuler:24.03-lts-sp4`）是否也遇到相同的 HTTP/2 流错误。
- 日志中 `#7`（stage-1 阶段）虽然也出现 HTTP/2 错误但最终未标记 FAILED——确认 stage-1 是否真正安装成功，还是仅因 #8 失败后被 `CANCELED` 中断而未报错。
