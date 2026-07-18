# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, MIRROR, No more mirrors to try

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
#8 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 软件仓库镜像在构建过程中持续出现 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），多个包（gcc-gfortran、glibc-devel、guile、gcc）下载均受影响，最终 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 在所有镜像源均重试失败后导致 dnf 安装退出，Docker 构建中断。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 这是 CI 基础设施问题（软件源镜像服务端 HTTP/2 连接不稳定）。PR 新增的 Dockerfile 从 docker pull 基础镜像到 dnf 元数据同步均正常，说明 Dockerfile 语法和构建逻辑本身没有错误。构建失败仅因在下载 RPM 包阶段，openEuler 24.03-LTS-SP4 的软件源镜像服务器端 HTTP/2 流被异常关闭，属于网络/服务端临时故障。

日志中也观察到，并行运行的 `[stage-1 2/4]`（最终阶段安装运行时依赖）同样遭遇了多次 `[MIRROR]` 错误（glibc-devel、gcc-gfortran），进一步确认这是整个软件源服务的系统性问题，而非该 Dockerfile 独有的问题。

## 修复方向

### 方向 1（置信度: 高）
**重试构建。** 这是软件源镜像服务端临时故障，PR 代码无需修改。等待 openEuler 24.03-LTS-SP4 软件源镜像服务恢复稳定后重新触发 CI 构建即可。若多次重试均失败，可考虑在 Dockerfile 的 `dnf install` 命令中添加 `--retries 5` 参数提高网络容错性，但这是治标不治本的规避手段，不应作为首要方案。

## 需要进一步确认的点
- 确认 `repo.****.org` 软件源镜像服务在构建时刻是否正在经历服务端异常或维护。Curl error 92（HTTP/2 流 INTERNAL_ERROR）通常是服务端问题，可检查 openEuler 镜像站的状态页面或联系镜像站运维确认。
- 验证其他同时刻使用 openEuler 24.03-LTS-SP4 基础镜像的 PR 构建是否也出现了相同的 HTTP/2 流错误，以确认这是全局性问题而非该 runner 节点孤立故障。
