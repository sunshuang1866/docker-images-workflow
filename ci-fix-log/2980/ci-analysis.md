# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败原因: CI 构建环境的 openEuler 24.03-LTS-SP4 RPM 仓库镜像在 HTTP/2 传输过程中发生流中断（Curl error 92: `HTTP/2 stream was not closed cleanly: INTERNAL_ERROR`），多个包（cmake-data、git-core、gcc-c++）下载失败。其中 `gcc-c++` 在所有可用镜像源上均下载失败，导致 `dnf install` 命令以 exit code 1 终止。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了 GrADS 2.2.3 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及相关元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `dnf install` 包列表语法正确、包名有效（`dnf` 依赖解析阶段成功列出了 258 个待安装包，未报告任何包名不存在或版本冲突）。构建失败完全由 openEuler 24.03-LTS-SP4 仓库镜像的网络传输异常导致，属于 CI 基础设施层面的瞬时性问题。

## 修复方向

### 方向 1（置信度: 高）
**重试构建。** 此失败为 openEuler 24.03-LTS-SP4 RPM 仓库镜像瞬时网络故障导致的 `dnf install` 下载中断，PR 代码本身无问题。Code Fixer 无需对 Dockerfile 做任何修改，直接在 CI 中触发重新构建即可。若重试后仍然失败，需由 CI 运维团队排查 openEuler 24.03-LTS-SP4 仓库镜像 `repo.****.org` 的 HTTP/2 服务端配置或网络链路稳定性。

## 需要进一步确认的点
| 序号 | 确认项 | 说明 |
|------|--------|------|
| 1 | 其他 PR 在同一时段是否也受此影响 | 若同时段有多个 PR 在同一仓库镜像上失败，可确认是仓库侧瞬时故障 |
| 2 | aarch64 架构构建 job 是否也失败 | 本日志仅含 x86_64 构建过程，aarch64 节点的仓库镜像状态未知 |
| 3 | 仓库镜像更换为 HTTP/1.1 是否可规避 | Curl error 92 在 HTTP/2 协议下发生，降级到 HTTP/1.1 可能作为规避手段（但应由 CI 运维决定） |
