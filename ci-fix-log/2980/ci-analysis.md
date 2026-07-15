# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install, gcc-c++

## 根因分析

### 直接错误
```
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

同样的 HTTP/2 流错误也出现在 `cmake-data`（行1199.1）和 `git-core`（行1776.2）的下载中，但这两个包在重试后成功下载，只有 `gcc-c++`（13MB，较大的包）在两次重试均失败后无更多镜像可用。

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-15`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件包仓库镜像在 HTTP/2 协议层发生流中断错误（`INTERNAL_ERROR (err 2)`），导致 `gcc-c++` 包下载失败。`dnf` 重试所有可用镜像后均未成功，构建中止。这是一个 CI 基础设施/网络层面的问题，与 PR 代码变更无关。

### 与 PR 变更的关联
PR 变更仅新增了一个 Dockerfile（grads 2.2.3 on openEuler 24.03-lts-sp4）及相关元数据文件，Dockerfile 中的 `dnf install` 命令是正确的——DNF 成功解析了所有 258 个依赖包，且 `cmake-data` 和 `git-core` 在重试后均成功下载。失败完全由 openEuler 仓库镜像的 HTTP/2 连接问题导致，与 PR 代码无关。

## 修复方向

### 方向 1（置信度: 高）
重试 CI 构建。这是一个典型的间歇性基础设施故障（仓库镜像 HTTP/2 流错误），`gcc-c++` 作为较大的包（13MB）在传输过程中更易受网络波动影响。同类错误（`cmake-data`、`git-core`）在重试后均成功，说明仓库本身可用，问题出在传输链路。通常重新触发 CI 流水线即可通过。

### 方向 2（置信度: 低）
如果重试持续失败，检查 CI runner 与 openEuler 24.03-LTS-SP4 仓库镜像之间的网络连接质量。可联系基础设施团队确认镜像站是否正在进行维护或存在已知的 HTTP/2 协议兼容性问题。也可以考虑在 Dockerfile 的 `dnf install` 前添加重试逻辑（如 `dnf install --setopt=retries=10`）以提高容错能力，但不建议为一次性基础设施抖动修改构建脚本。

## 需要进一步确认的点
- 确认该仓库镜像（`repo.****.org`）在 CI 构建期间的 HTTP/2 服务状态是否正常
- 确认同一 CI runner 上其他使用 openEuler 24.03-LTS-SP4 的构建是否存在类似的 `gcc-c++` 下载失败（以判断是普遍问题还是偶发故障）
- 如果重试后仍然失败，确认 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 在镜像站是否确实可达
