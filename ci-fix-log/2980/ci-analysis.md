# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, HTTP/2 stream, INTERNAL_ERROR, No more mirrors to try

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
- 失败原因: CI 构建环境中 openEuler 24.03-LTS-SP4 软件仓库镜像在下载大体积 RPM 包（`gcc-c++` 约 13MB、`cmake-data` 约 2.1MB、`git-core` 约 11MB）时频繁触发 HTTP/2 流关闭异常（`Curl error (92): INTERNAL_ERROR`），DNF 耗尽所有镜像后放弃下载，导致 `dnf install` 退出码为 1。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 GrADS 2.2.3 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及相关元数据文件，Dockerfile 中的 `dnf install` 命令包列表和语法均正确。失败是 openEuler 软件仓库镜像的网络基础设施不稳定导致的，属于瞬态 CI 基础设施故障。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重试 CI 即可。** 这是一个 CI 基础设施问题——openEuler 软件仓库的反向代理/CDN 在处理 HTTP/2 大文件传输时出现流中断。等待仓库恢复后重新触发 CI 构建即可。如果问题持续出现，可考虑在 Dockerfile 的 `dnf install` 前添加 `--retries` 或重试逻辑以提高鲁棒性。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 软件仓库当前是否已恢复正常（可在另一时间段重试 CI 验证）
- 如果重试后相同错误反复出现，可能需要在 CI 构建环境中排查仓库镜像节点的连接质量

## 修复验证要求
无 — 此失败为 infra-error，无需对 PR 代码做任何修改。
