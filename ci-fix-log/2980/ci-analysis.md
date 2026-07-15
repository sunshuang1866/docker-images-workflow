# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF 镜像 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: CI 构建环境中，openEuler 24.03-LTS-SP4 的 RPM 仓库镜像站存在 HTTP/2 协议层面的连接问题（`INTERNAL_ERROR`），导致 `gcc-c++` 包的多次下载尝试均以 Curl error (92) 失败。注意：`cmake-data` 和 `git-core` 也曾遇到同类 HTTP/2 流错误，但通过重试成功下载；`gcc-c++` 重试后全部镜像耗尽，最终失败。

### 与 PR 变更的关联
与 PR 代码变更**无关**。PR 新增的 Dockerfile 语法、包名和构建逻辑均无问题。失败完全由 `dnf install` 阶段从 `repo.****.org` 仓库下载 RPM 包时的网络基础设施故障（HTTP/2 流中断）导致。这是一个非代码层面的 CI 环境/镜像站可靠性问题。

## 修复方向

### 方向 1（置信度: 高）
重试 CI。该失败由 openEuler 24.03-LTS-SP4 仓库镜像站的临时 HTTP/2 流中断引起，与 PR 代码无关。等待镜像站恢复后重新触发 CI 构建即可。若持续复现，可考虑在该 Dockerfile 的 `dnf install` 命令中添加 `--retries 5` 参数或显式设置 `http2=false` 的 dnf 配置来增强网络容错能力。

## 需要进一步确认的点
- 同一时间段其他使用 openEuler 24.03-LTS-SP4 基础镜像的 PR 是否同样失败——如果是，则确认镜像站存在普遍性问题而非孤立事件。
- `repo.****.org` 镜像站的 HTTP/2 服务状态及是否有已知的间歇性中断报告。

## 修复验证要求
无需验证（infra-error，非代码修复）。
