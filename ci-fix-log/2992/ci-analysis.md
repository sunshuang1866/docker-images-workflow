# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Stream error, INTERNAL_ERROR, No more mirrors to try

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
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像服务器在处理 HTTP/2 流时频繁返回 `INTERNAL_ERROR`（Curl error 92），导致多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）下载失败；其中 `gcc` 包（34MB）在耗尽所有镜像重试后仍未成功，dnf 最终报错退出。

### 与 PR 变更的关联
与 PR 代码变更**无直接关联**。PR 仅新增了一个标准的多阶段构建 Dockerfile（使用 `openeuler/openeuler:24.03-lts-sp4` 基础镜像、通过 `dnf install` 安装编译依赖），Dockerfile 语法和包名均无错误。失败原因是 openEuler 24.03-LTS-SP4 仓库的 HTTP/2 服务器端协议错误，属于 CI 基础设施问题。同一构建任务中，其他镜像使用 SP3 仓库的 dnf 命令（如日志中预检阶段的 `Package python3-dnf-4.16.2-10.oe2403sp4.noarch is already installed.`）均正常运行。

## 修复方向

### 方向 1（置信度: 中）
**重试 CI 任务**。HTTP/2 stream error (`INTERNAL_ERROR`) 通常是仓库服务器端的临时性问题（如服务过载、HTTP/2 连接管理缺陷），而非 PR 代码问题。等待仓库服务恢复后重新触发 CI 构建即可。若多次重试均失败，则可能是该仓库镜像的 HTTP/2 实现存在持续性问题，需联系仓库运维团队排查服务端。

### 方向 2（置信度: 低）
**降级到 HTTP/1.1**。Dockerfile 本身不需要修改，但若能影响 CI runner 的 dnf/curl 配置（如在 `dnf.conf` 中设置 `http2=false` 或 `max_parallel_downloads=1`），可绕过 HTTP/2 层的服务端 bug。但这属于 CI 基础设施配置变更，应由 CI 运维团队评估，**不属于 code-fixer 的修复范围**。

## 需要进一步确认的点
- 该 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 服务是否为已知问题（可查阅运维告警或历史上报）。
- 同一 CI 环境中其他使用 SP4 仓库的镜像（如已存在的 `Others/multiwfn/cb37c53/24.03-lts-sp3` 同级目录无 SP4 可对比，需找其他 SP4 镜像交叉验证）是否也遇到同类 HTTP/2 错误，以确认是泛化问题还是偶发。
- 若其他 SP4 镜像的 dnf 安装均正常通过，则需确认本次构建的 runner 网络环境是否有中间设备干扰 HTTP/2 流量。
