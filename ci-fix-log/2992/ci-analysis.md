# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像仓库HTTP2错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: CI 构建环境的 openEuler 24.03-LTS-SP4 软件包镜像仓库（`repo.****.org`）持续返回 HTTP/2 framing 层流错误（Curl error 92: INTERNAL_ERROR），导致多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc 等）反复下载失败，最终所有镜像均尝试完毕后 `dnf` 放弃安装。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个 Dockerfile 及对应的元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 中的 `dnf install` 命令格式与已有 sp3 版本完全一致，失败原因是 CI 基础设施的软件包镜像仓库存在 HTTP/2 协议层面的故障，属于临时的网络/服务端问题。

另外值得注意的是，日志中 `#7`（stage-1 层，安装 gcc-gfortran/make/openblas-devel/lapack-devel 的 `dnf install`）也出现了同类 Curl error (92) 但最终似乎重试成功（未见其 FAILED），而 `#8`（builder 层，额外安装 git/gcc/gcc-c++，因此有更多包依赖）在多个包上都遭遇了该错误并最终耗尽所有镜像。这说明镜像仓库的 HTTP/2 故障是间歇性的，而非完全不可用，但在需要下载 157 个包的 builder 场景中累积导致失败的概率更高。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码。** 这是 CI 基础设施中 openEuler 24.03-LTS-SP4 软件包镜像仓库的临时 HTTP/2 协议故障。应重新触发 CI 构建（retry），等待镜像仓库恢复后即可通过。如果反复复现，则需要运维团队排查 `repo.****.org` 的 HTTP/2 反向代理/负载均衡配置。

## 需要进一步确认的点
- 该镜像仓库（`repo.****.org`）的 HTTP/2 故障是否为偶发性或持续性问题，可对比同期其他使用 openEuler 24.03-lts-sp4 的 PR 构建是否也失败。
- 如果 retry 后仍然失败，可能需要检查仓库 URL 是否已变更或需要切换到备用镜像源。
