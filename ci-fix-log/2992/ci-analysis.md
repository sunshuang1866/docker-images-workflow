# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤，builder stage）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 连接不稳定，多个包（gcc-gfortran、glibc-devel、guile、gcc）下载时频繁出现 Curl error (92) — HTTP/2 流未正常关闭 (INTERNAL_ERROR)。gcc 包（34 MB）在多次重试后仍无法下载且所有镜像均被尝试完毕，导致 `dnf install` 以 exit code 1 失败。同时 stage-1（`#7`）的 `dnf install` 也出现相同类型的 HTTP/2 错误。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`（以及对应的 README、image-info.yml、meta.yml 条目），Dockerfile 内容与已有的 `24.03-lts-sp3` 版本结构一致，`dnf install` 包列表完全相同。失败是 openEuler 24.03-LTS-SP4 仓库镜像服务器的 HTTP/2 基础设施问题导致的，属于 CI 外部依赖不稳定。

## 修复方向

### 方向 1（置信度: 高）
这是 CI 基础设施问题，与代码无关。openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 服务当前不稳定。等待仓库镜像服务恢复后重新触发 CI 构建即可。Code Fixer 无需做任何代码修改。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 服务是否已恢复正常（可与其他使用同版本基础镜像的近期成功 PR 交叉验证）
- 检查仓库镜像是否对 HTTP/2 连接有速率限制或其他保护策略，如持续出现可考虑在 `dnf install` 前添加 `--setopt=keepcache=1` 或切换到 HTTP/1.1
