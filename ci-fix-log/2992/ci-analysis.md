# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 镜像仓库HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（builder 阶段的 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库（`repo.****.org`）在 CI 构建期间出现多次 HTTP/2 流层错误（`Curl error 92: INTERNAL_ERROR`），导致多个 RPM 包下载失败。最终 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 耗尽所有镜像重试次数后彻底失败，`dnf install` 以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`（一个标准的 openEuler 应用镜像 Dockerfile）、更新了 `meta.yml` 注册新 tag，以及更新了 README 和 image-info.yml 文档。新增 Dockerfile 中的 `dnf install` 命令语法正确，安装的包（git、gcc、gcc-c++、gcc-gfortran、make、openblas-devel、lapack-devel）均为 openEuler 24.03-LTS-SP4 官方仓库中的标准包。失败完全是 CI 构建时软件仓库 HTTP/2 连接不稳定所致。

值得注意的是：PR 中新增的 Dockerfile 与同仓库已有的 `24.03-lts-sp3` 版本（`Others/multiwfn/cb37c53/24.03-lts-sp3/Dockerfile`）结构一致，仅基础镜像 tag 从 `24.03-lts-sp3` 变为 `24.03-lts-sp4`，包安装命令完全相同，进一步说明此次失败与代码变更无关。

## 修复方向

### 方向 1（置信度: 中）
**基础设施问题，Code Fixer 无需处理。** 这是 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 服务器端间歇性故障。等待仓库基础设施恢复后重试 CI 构建即可。可通过手动触发 re-run 验证是否恢复。

### 方向 2（置信度: 低）
如果仓库镜像 HTTP/2 问题持续存在，可考虑在 Dockerfile 中为 `dnf` 添加重试参数（如 `dnf install --setopt=retries=10 ...`）或禁用 HTTP/2（`echo "http2=false" >> /etc/dnf/dnf.conf`）作为临时绕过手段。但此方向仅为规避方案，不应作为永久修复。

## 需要进一步确认的点
1. **openEuler 24.03-LTS-SP4 仓库状态**：需确认 `repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/` 路径下的 HTTP/2 服务是否已恢复稳定。建议在 CI runner 上手动执行 `curl -v https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 验证当前可达性。
2. **aarch64 架构构建日志**：当前日志仅来自 x86-64 runner（`ecs-build-docker-x86-03-sp`）。`meta.yml` 中该 tag 同时声明支持 `amd64, arm64`，需确认 aarch64 runner 上是否也遇到同样的仓库问题。
3. **SP3 是否正常**：建议对比同仓库 `cb37c53-oe2403sp3` tag 的最新构建状态，确认问题是否仅限于 SP4 仓库。

## 修复验证要求
无。本次失败为 infra-error，不涉及代码修改，无需验证步骤。
