# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, MIRROR, No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 37 ... INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 15 ... INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 43 ... INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 27 ... INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `RUN dnf install` 步骤）
- 失败原因: CI 构建环境中 dnf 从 openEuler 24.03-LTS-SP4 官方 RPM 仓库下载软件包时，多个包（gcc-gfortran、glibc-devel、guile、gcc）反复遭遇 HTTP/2 协议层 `INTERNAL_ERROR`（curl error 92），最终 gcc-12.3.1 (34 MB) 在所有镜像均重试耗尽后仍然下载失败，导致整个 dnf install 命令以 exit code 1 终止。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 的改动仅限于：
1. 新增 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`（一个标准的 dnf install + git clone + make 构建流程）
2. 更新 `meta.yml`、`README.md`、`image-info.yml` 以注册新镜像

Dockerfile 中的 `dnf install` 命令语法正确、包名均有效（日志中 dnf 成功解析了依赖关系并开始下载 157 个包）。失败发生在 RPM 包下载阶段，根因是 openEuler 24.03-LTS-SP4 仓库的 CDN/镜像源服务器端 HTTP/2 协议实现问题，与 PR 的代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试 / 等待上游基础设施恢复。** 该失败是 openEuler 24.03-LTS-SP4 RPM 仓库镜像源的临时性网络/协议故障（HTTP/2 流异常关闭），属于 CI 基础设施问题。日志中多个包在重试后成功下载（如 #7 的 stage-1 阶段 glibc-devel 经一次 `[MIRROR]` 错误后重试成功），表明仓库间或有恢复能力但本次构建中 gcc 大包（34 MB）在持续的 HTTP/2 错误下最终耗尽重试次数。处理方式：`@openeuler/ci-infra` 团队确认 24.03-LTS-SP4 仓库状态正常后，重新触发 CI 构建。

### 方向 2（置信度: 中）
**在 Dockerfile 中为 dnf 添加 `--retries` 参数增加重试韧性。** 如果该 HTTP/2 协议错误是 24.03-LTS-SP4 仓库的持续性问题（而非临时抖动），可在 Dockerfile 的 `dnf install` 命令中添加 `--setopt=retries=10` 或类似参数提高网络容错能力。但此方向需要在确认问题持续复现后才考虑，优先建议先重试 CI 确认是否为临时故障。

## 需要进一步确认的点
1. 确认 openEuler 24.03-LTS-SP4 的 RPM 仓库（`repo.openeuler.org` 或镜像站）在构建发生时段是否存在 HTTP/2 协议抖动或服务降级。
2. 确认是否是 CI 构建节点（`ecs-build-docker-x86-03-sp`）与仓库之间的网络链路问题（例如中间代理对 HTTP/2 长连接的不当处理）。
3. 若多次重试仍失败，需排查是否为 24.03-LTS-SP4 仓库的 curl HTTP/2 兼容性已引入持久性问题，可能需要将 dnf 降级为 HTTP/1.1 协议（`http2=false`）。

## 修复验证要求
无。该失败为 infrastructure 类型，无需 code-fixer 提交代码修改。
