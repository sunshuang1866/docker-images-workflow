# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2传输错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, HTTP/2 stream, INTERNAL_ERROR, No more mirrors to try, Error downloading packages

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 软件源（`repo.****.org`）在 HTTP/2 传输层出现服务器端内部错误（`INTERNAL_ERROR err 2`），导致多个 RPM 包（cmake-data、git-core、gcc-c++）下载失败，其中 `gcc-c++` 在所有镜像重试后仍无法下载，`dnf install` 整体失败。

### 与 PR 变更的关联
**与 PR 变更无关**。该 PR 仅新增了一个 GrADS 2.2.3 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `dnf install` 命令格式正确，列出的所有软件包名称在 openEuler 24.03-LTS-SP4 仓库中均存在（依赖解析阶段成功完成，列出了 258 个待安装包）。失败完全由 RPM 仓库服务器的 HTTP/2 传输故障引起，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码**。这是 openEuler RPM 镜像站 `repo.****.org` 的临时性 HTTP/2 传输故障。应在镜像站恢复后**重新触发 CI 构建**（retry/rerun）。若该镜像站持续不稳定，可考虑在 Dockerfile 的 `dnf install` 之前添加仓库配置步骤，使用备选镜像源（如 `mirrors.tuna.tsinghua.edu.cn` 或 `mirrors.aliyun.com`）。

## 需要进一步确认的点
1. openEuler 24.03-LTS-SP4 RPM 仓库（`repo.****.org`）在构建时段的可用性状态——是否为临时性中断还是持续性问题。
2. 该仓库是否对 CI 构建环境（`ecs-build-docker-x86-03-sp`）的 IP 段存在限流或连接策略。
3. 同一时段该仓库的其他 CI job（如其他 PR 对 24.03-LTS-SP4 的构建）是否也出现同类 HTTP/2 流错误，以确认是否为仓库端的全局性问题。
