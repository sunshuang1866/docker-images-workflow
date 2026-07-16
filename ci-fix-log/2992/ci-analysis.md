# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: CI 构建环境在执行 `dnf install` 从 openEuler 24.03-LTS-SP4 仓库镜像站下载 RPM 包时，遭遇持续性的 HTTP/2 流层协议错误（Curl error 92: `INTERNAL_ERROR`），多个包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）均受影响。其中 `gcc` 包在所有镜像站重试后全部失败，导致 dnf 事务中断，Docker 构建退出码 1。

### 与 PR 变更的关联
**与 PR 变更无关。** 此次 PR 只新增了 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile` 及相关元数据文件（README、image-info.yml、meta.yml），Dockerfile 中的 `dnf install` 命令语法正确、包名合法。失败纯粹因为 openEuler 24.03-LTS-SP4 官方仓库镜像站在 CI 构建时段出现了 HTTP/2 协议层通信故障，导致 RPM 包下载失败。同时构建的两个阶段（builder 阶段 #8 和 stage-1 阶段 #7）均在从同一仓库下载时遭遇相同的 Curl error (92)，进一步确认是仓库侧基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复，只需重新触发 CI。** 这是典型的 infra-error，根因是 openEuler 24.03-LTS-SP4 仓库镜像站在构建时段存在 HTTP/2 协议稳定性问题。等待仓库恢复后重新运行 CI 流水线应可通过。若问题持续出现，可考虑在 Dockerfile 的 `dnf install` 命令中添加 `--retries` 或调整 dnf 配置的 `max_retries` 参数以增强网络波动容忍度。

## 需要进一步确认的点
- 在同一时段，其他依赖 openEuler 24.03-LTS-SP4 仓库的 PR 构建是否也出现相同错误——若是，可确认是仓库镜像站的普遍性问题而非个案。
- 若重新触发 CI 后仍然失败，需要确认 `repo.****.org` 是否对 CI 构建环境的 IP 有访问限制或速率限制。
