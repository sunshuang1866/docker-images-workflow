# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, dnf install, No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`RUN dnf install ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 yum/dnf 软件包镜像源在下载大文件（gcc 34MB、gcc-gfortran 13MB、guile 6.3MB）时反复出现 HTTP/2 流错误（Curl error 92），多次重试后耗尽所有可用镜像，最终 dnf 无法下载 `gcc-12.3.1-110.oe2403sp4.x86_64` 包而导致构建失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 的改动仅为添加 multiwfn 在 24.03-lts-sp4 上的新 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 内容本身（`dnf install` 包列表、构建步骤）与已有的 sp3 版本完全一致。失败根因是 openEuler 24.03-LTS-SP4 软件包镜像源在 CI 构建期间存在 HTTP/2 层网络不稳定问题，属于基础设施故障。日志中 `#7`（stage-1 阶段）也出现了相同的 Curl error (92)，进一步印证这是镜像源的系统性问题而非个别软件包或 Dockerfile 写法问题。

## 修复方向

### 方向 1（置信度: 高）
此失败为 CI 基础设施问题（openEuler 24.03-LTS-SP4 软件包镜像源 HTTP/2 连接不稳定），无需修改 PR 代码。Code Fixer 无需处理，建议触发重新构建（retry）以验证镜像源恢复后的构建结果。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 的 `repo.****.org` 镜像源当前 HTTP/2 服务状态是否正常（可与运维团队确认或等待镜像源恢复后重试）。
- 若多轮重试后仍然失败，需确认是否需要将 dnf repo 源切换为其他替代镜像站（如清华镜像站 mirrors.tuna.tsinghua.edu.cn）。

## 修复验证要求
（不适用 — 此失败为 infra-error，无需代码修复。）
