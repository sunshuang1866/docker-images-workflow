# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤，builder 阶段）
- 失败原因: openEuler 24.03-LTS-SP4 官方仓库 (`repo.****.org`) 在处理 HTTP/2 请求时反复出现流帧错误（`Curl error (92)`），多个 RPM 包的下载均被中断，DNF 在耗尽所有镜像重试后安装失败。构建中的两个阶段（builder `#8` 和 stage-1 `#7`）均受此影响，后者在 builder 失败后被 CANCELED。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了针对 openEuler 24.03-lts-sp4 的 Dockerfile 及相关元数据（README.md、image-info.yml、meta.yml），Dockerfile 中的 `dnf install` 命令语法正确，依赖包列表与其他已有的 sp3 版本一致。失败完全由 openEuler 软件仓库侧 HTTP/2 服务不稳定导致，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
此失败无需修改 PR 代码。需要 CI 运维人员排查 `repo.****.org` 仓库的 HTTP/2 服务状态，或等待仓库恢复后重试构建。如果仓库 HTTP/2 问题持续存在，可考虑在 Dockerfile 中临时禁用 DNF 的 HTTP/2（例如在 `dnf install` 前设置 `echo "http2=false" >> /etc/dnf/dnf.conf`）作为规避手段，但此为权宜之计，不应合入仓库。

## 需要进一步确认的点
- 确认 `repo.****.org` 的 HTTP/2 服务当前状态，是否为临时故障还是已知持续性问题
- 确认同仓库其他使用 `openEuler 24.03-lts-sp4` 基础镜像的构建是否也出现相同问题（以判断是否为本次构建特例）
- 如果重试后构建仍失败，确认是否需要更换镜像源或添加备用镜像

## 修复验证要求
无。此失败为 infra-error，PR 代码本身无需修改。若重试后构建成功即验证通过。
