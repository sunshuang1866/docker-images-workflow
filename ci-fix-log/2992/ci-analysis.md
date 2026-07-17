# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install, MIRROR, FAILED

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): ... [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): ... [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): ... [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): ... [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `dnf install` 步骤）
- 失败原因: CI 构建环境中 `dnf install` 从 openEuler 24.03-LTS-SP4 软件仓库下载 RPM 包时，仓库镜像返回持续的 HTTP/2 流协议错误（Curl error 92），多个包（gcc-gfortran、glibc-devel、guile、gcc）下载重试均失败，最终 `gcc` 包的镜像重试次数耗尽，`dnf` 报错退出（exit code: 1）。此为 CI 基础设施/网络问题，与 PR 代码变更无关。

### 与 PR 变更的关联
PR 变更仅新增了 `cb37c53/24.03-lts-sp4/Dockerfile` 及其对应的元数据文件和 README 条目，Dockerfile 中 `dnf install` 命令语法正确、包名无误。失败完全由 openEuler 24.03-LTS-SP4 软件仓库镜像在构建时段的 HTTP/2 协议不稳定所致，构建环境中的网络层问题导致 RPM 包下载失败。**PR 代码变更不是失败原因。**

## 修复方向

### 方向 1（置信度: 高）
重新触发 CI 构建。此失败为 transient infra-error（仓库镜像临时的 HTTP/2 协议异常），Dockerfile 本身没有错误。在仓库镜像恢复正常后，重新运行 CI 流水线即可通过。

### 方向 2（置信度: 低）
若重试后仍持续失败，可将 Dockerfile 中 `dnf install` 命令添加 `--retries` 参数提高容错能力，或将仓库 baseurl 显式切换为 HTTP/1.1（禁用 HTTP/2）。但通常重试 1-2 次即可解决此类临时性镜像协议错误。

## 需要进一步确认的点
无。日志信息充分，根因明确——openEuler 仓库镜像在构建时段的 HTTP/2 连接不稳定导致 RPM 下载失败，属于 CI 基础设施问题。
