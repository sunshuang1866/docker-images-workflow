# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP2流错误
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
ERROR: failed to solve: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 包仓库（`repo.****.org`）在 CI 构建时出现 HTTP/2 流层错误（Curl error 92），多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）下载过程中 HTTP/2 stream 被非正常关闭（INTERNAL_ERROR），重试后耗尽所有镜像源，最终 `gcc` 包下载失败导致 `dnf install` 命令退出码为 1。这是 CI 基础设施/上游仓库的网络问题，与 PR 代码变更无关。

### 与 PR 变更的关联
PR 变更仅包括：
1. 新增 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`（47 行，首次为该版本添加构建文件）
2. 更新 `Others/multiwfn/README.md`、`Others/multiwfn/doc/image-info.yml`、`Others/multiwfn/meta.yml` 以注册新镜像

Dockerfile 语法和 `dnf install` 包名均正确无误。构建失败的唯一原因是在下载阶段 `repo.****.org` 持续返回 HTTP/2 流错误，与 PR 的代码/配置变更**无直接关联**。

值得注意的是：`#7`（stage-1 第二阶段，安装 32 个包）也遇到了同样的 `gcc-gfortran` 和 `glibc-devel` HTTP/2 流错误，虽然部分包重试成功，但最终在 `#8`（builder 第一阶段，安装 157 个包）失败后，`#7` 也被取消（`#7 CANCELED`）。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 此失败为 infra-error，根因是 openEuler 24.03-LTS-SP4 RPM 仓库在构建时段出现 HTTP/2 服务端流异常。Code Fixer 无需修改任何文件。建议在仓库服务恢复正常后**重新触发 CI 构建**（retry）。

## 需要进一步确认的点
- 确认 `repo.****.org` 的 openEuler 24.03-LTS-SP4 仓库在当前时段是否已恢复正常（可手动 `curl` 测试）。
- 如果 re-trigger 后仍然失败，需要排查是否是 24.03-LTS-SP4 仓库端持续存在 HTTP/2 配置问题（如反向代理层 HTTP/2 流管理 bug），届时可能需要联系仓库运维团队。

## 修复验证要求
不适用（infra-error，无修复代码）。
