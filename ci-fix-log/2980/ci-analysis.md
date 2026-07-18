# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像在下载 RPM 包时反复出现 HTTP/2 协议层流错误（Curl error 92: `INTERNAL_ERROR`）。共 258 个待安装包中，`cmake-data`、`git-core`、`gcc-c++` 三个包遭遇了该错误。前两者重试后成功，`gcc-c++`（13 MB）连续两次重试均失败，最终所有镜像尝试耗尽，`dnf install` 整体失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个 GrADS Dockerfile（声明了标准编译依赖）、更新了 README.md 表格、image-info.yml 和 meta.yml。失败发生在 `dnf install` 从 openEuler 官方仓库下载系统包阶段，是 CI 构建环境中与仓库镜像之间的网络/协议层基础设施问题。Dockerfile 中声明的包列表本身正确无误——依赖解析阶段已完成（`Dependencies resolved.`），下载至 1970 秒时因协议错误中断。

## 修复方向

### 方向 1（置信度: 高）
**无需修复代码，重新触发 CI 构建即可。** 该失败为 transient（暂时性）网络基础设施问题——openEuler 24.03-LTS-SP4 仓库镜像在构建时段出现 HTTP/2 协议层故障。`cmake-data` 和 `git-core` 的重试成功表明问题具有间歇性。Code Fixer 无需处理。

### 方向 2（置信度: 中）
若多次重试 CI 均失败，可考虑在 Dockerfile 的 `dnf install` 命令中添加 `--retries 5`（或更高）以增加网络波动容忍度，或显式指定其他可用的镜像站。但这属于优化措施而非必要修复，且当前日志已显示 dnf 已自动尝试了多个 mirror。

## 需要进一步确认的点
- 该时段 openEuler 24.03-LTS-SP4 仓库是否存在已知的网络/服务中断
- 构建节点 `ecs-build-docker-x86-03-sp` 到 `repo.****.org` 的网络链路是否稳定
- 其他使用同一基础镜像（`openeuler/openeuler:24.03-lts-sp4`）的 PR 是否也遭遇了类似失败（用于判断是全局性还是局部性问题）
