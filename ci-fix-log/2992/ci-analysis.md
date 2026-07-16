# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try

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
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤，builder 阶段）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在 Docker 构建过程中出现 HTTP/2 协议层流错误（Curl error 92），多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）下载因 HTTP/2 流未正常关闭而重试，最终 gcc 包耗尽所有镜像源后彻底失败，dnf 安装命令退出码为 1。两个并行构建阶段（builder #8 和 stage-1 #7）同时受影响，说明这是仓库侧的网络问题而非单次偶发波动。

### 与 PR 变更的关联
**无关**。PR 变更仅包含：
1. 新增 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`（sp4 版本的构建文件）
2. 更新 `Others/multiwfn/README.md`、`doc/image-info.yml`、`meta.yml`（文档+注册新镜像条目）

所有变更均为纯文件和元数据，不涉及任何可能影响 RPM 仓库连接性的配置。失败发生在 `dnf install` 从外部仓库下载包阶段，这是 CI 基础设施侧的仓库镜像网络问题，与本次 PR 的代码改动无任何因果关联。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，触发重试即可。** 该失败属于 openEuler 24.03-LTS-SP4 RPM 仓库镜像的临时网络故障（HTTP/2 流异常关闭），与 PR 代码无关。等待仓库镜像恢复后重新触发 CI 构建（retry job）应可正常通过。

### 方向 2（置信度: 低）
**更换 dnf 镜像源。** 如果该仓库镜像持续不稳定，可在 Dockerfile 的 `dnf install` 之前添加 `sed` 替换 repo 文件中 mirrorlist/baseurl 为其他更稳定的镜像站。但这属于基础设施层面的工作，不应由本次 PR 承担。

## 需要进一步确认的点
- 确认 `repo.****.org` 服务器在构建时段是否有已知的 HTTP/2 协议问题或维护窗口。
- 确认同批次其他使用 openEuler 24.03-LTS-SP4 基础镜像的镜像构建是否也出现了类似的 Curl error (92)，以判断这是全局性问题还是该特定仓库镜像节点的问题。
