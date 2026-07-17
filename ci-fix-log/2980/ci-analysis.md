# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try

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
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像在 HTTP/2 传输层出现流错误（Curl error 92: INTERNAL_ERROR），导致多个 RPM 包（cmake-data、git-core、gcc-c++）下载时连接被服务端非正常关闭。其中 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 在两次重试后所有可用镜像均失败，dnf 无法完成安装，构建中止。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增一个 Dockerfile（GrADS 2.2.3 on openEuler 24.03-LTS-SP4）及配套的 README、image-info.yml、meta.yml 元数据更新。Dockerfile 中 `dnf install` 命令语法正确、包名正确。失败纯粹是 CI 构建时 openEuler 官方仓库镜像的 HTTP/2 传输层出现网络故障，属于外部基础设施临时性问题。3 个不同包（cmake-data、git-core、gcc-c++）先后遭遇相同的 `Curl error (92)` 可印证这是仓库端问题而非特定包问题；其中 cmake-data 和 git-core 重试后成功，仅 gcc-c++ 最终耗尽所有镜像。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 openEuler 24.03-LTS-SP4 仓库镜像的临时性网络故障（HTTP/2 流中断），与 PR 变更无关。建议触发 CI 重试（re-run），待仓库镜像恢复正常后即可通过。若多次重试均在同一包失败，可考虑在 Dockerfile 中为 `dnf install` 添加 `--retries 5` 等重试参数以增强鲁棒性。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）在当时是否存在已知的 HTTP/2 服务异常或维护事件。
- 若重新触发 CI 后仍然失败且在新的包上出现相同 Curl error (92)，考虑是否需要将 dnf 配置中的 HTTP/2 回退到 HTTP/1.1 或更换镜像源。
