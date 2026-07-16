# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: HTTP/2镜像站流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Stream error, INTERNAL_ERROR, rpm download, dnf install, No more mirrors to try

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（dnf install 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 软件包镜像站在通过 HTTP/2 协议传输较大软件包（cmake-data、git-core、gcc-c++）时，多次出现 HTTP/2 流被非正常关闭（`INTERNAL_ERROR (err 2)`）的协议层错误，dnf/Curl 重试所有可用镜像后全部失败，导致 `dnf install` 无法完成。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 仅新增了一个标准的 Dockerfile（安装编译依赖、克隆源码、构建安装 GrADS）以及配套的 README、image-info.yml、meta.yml 元数据文件。Dockerfile 中的 `dnf install` 命令语法正确，失败完全由 openEuler 软件包镜像站的 HTTP/2 服务端协议错误导致。dnf 在下载 258 个 RPM 包的过程中，其中 3 个较大包（cmake-data 2.1MB、git-core 11MB、gcc-c++ 13MB）遇到 HTTP/2 stream 异常终止，重试耗尽后失败。其余 255 个包（含 gcc 34MB）下载成功。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 这是 CI 基础设施问题，openEuler 24.03-LTS-SP4 的 RPM 镜像站在当前时段存在 HTTP/2 协议层面的不稳定，导致 HTTP/2 stream 被服务端非正常关闭（`INTERNAL_ERROR`）。应当重试 CI 构建任务（re-trigger），期望镜像站恢复正常后构建通过。

### 方向 2（置信度: 低，仅在重试持续失败时考虑）
若多次重试仍持续失败，可在 Dockerfile 的 `dnf install` 命令中添加 `--setopt=retries=10` 或降低并发下载数（`--setopt=max_parallel_downloads=4`）以提高容错性。但本质上这不是 Dockerfile 的问题，属于服务端修复范畴。

## 需要进一步确认的点
1. 确认 openEuler 24.03-LTS-SP4 OS 仓库镜像站当前的 HTTP/2 服务健康状况（该错误可能与特定 CDN 节点或反向代理的 HTTP/2 实现有关）。
2. 确认该问题是否为偶发性（重试后是否通过），若为持续性故障，需联系 openEuler 基础设施团队修复镜像站。
3. 确认其他同样使用 `24.03-lts-sp4` 基础镜像的 Dockerfile 是否也出现同类错误，以判断问题影响范围。
