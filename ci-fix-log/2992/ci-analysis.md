# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2连接异常
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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
#8 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（`RUN dnf install -y git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel`）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在本次 CI 运行期间出现 HTTP/2 协议层连接异常（Curl error 92: stream was not closed cleanly: INTERNAL_ERROR），导致 `gcc` 等多个软件包下载失败。所有可用镜像均被尝试后仍失败，dnf 安装步骤以退出码 1 终止。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了 multiwfn 的 Dockerfile（24.03-lts-sp4 版本）、更新了 README.md、image-info.yml 和 meta.yml。Dockerfile 内容为标准的多阶段构建流程（`dnf install` 构建依赖 → `git clone` → `sed` 修改 Makefile → `make noGUI`），不存在语法错误或错误的依赖声明。失败纯粹由 CI 运行时 openEuler 仓库镜像的网络波动造成，属于基础设施问题。

此外，日志中 `#7`（stage-1 的 `dnf install`）也出现了相同模式的 HTTP/2 流错误（`[MIRROR] glibc-devel`、`[MIRROR] gcc-gfortran`），进一步证实问题出在镜像服务端而非 Dockerfile 配置。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复，重新触发 CI 即可。** 该失败属于 openEuler 仓库镜像的暂时性网络波动（HTTP/2 协议层连接异常），与 PR 代码变更无关。直接重新触发 CI 流水线（retry/re-run）大概率可以通过。如果连续多次重试仍失败，需联系 openEuler 镜像站运维确认 24.03-LTS-SP4 仓库的 HTTP/2 服务是否正常。

## 需要进一步确认的点
- 本次镜像 `repo.****.org` 是否有其他同时段的 CI 构建也出现了同类 HTTP/2 错误（可交叉验证是否为仓库侧全局性问题）。
- 如果重试仍持续失败，需确认 openEuler 24.03-LTS-SP4 的 OS 仓库中 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 是否仍存在于此镜像站上。
