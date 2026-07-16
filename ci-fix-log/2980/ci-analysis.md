# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: HTTP/2流中断导致RPM下载失败
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
```

### 根因定位
- 失败位置: Dockerfile:6（`RUN dnf install -y` 步骤）
- 失败原因: CI 构建环境访问 openEuler 24.03-LTS-SP4 软件仓库镜像时，HTTP/2 传输层发生多次流中断（`INTERNAL_ERROR (err 2)`），部分 RPM 包（cmake-data、git-core）在重试后成功下载，但 `gcc-c++`（13MB）在两次流中断后所有镜像均被尝试且失败，`dnf` 无法安装全部依赖而退出。

### 与 PR 变更的关联
**与 PR 变更无关**。本次 PR 仅新增了一个标准格式的 Dockerfile（安装需要的编译依赖）和元数据文件。Dockerfile 中的 `dnf install` 命令语法正确、依赖列表完整——日志中 "Dependencies resolved" 显示 258 个包均已被 dnf 成功解析，证明仓库中存在这些包。失败完全是网络层面的 HTTP/2 流中断问题，属于 CI 基础设施的临时性故障，在任何仓库、任何合法 Dockerfile 构建中都可能偶发。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修改，重新触发 CI 构建即可**。HTTP/2 流中断是网络基础设施的瞬时问题，与 Dockerfile 内容和 PR 代码无关。`cmake-data`（2.1MB）和 `git-core`（11MB）在首次流中断后重试均成功，`gcc-c++`（13MB）仅因两次中断后镜像重试耗尽而失败。在后续 CI 运行中，网络条件正常时应能通过。

## 需要进一步确认的点
- 如果反复重试多次（≥3 次）均失败，则需要检查 openEuler 24.03-LTS-SP4 仓库镜像 `repo.****.org` 的 HTTP/2 配置或镜像稳定性，确认是否存在服务端问题而非客户端网络波动。
