# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库 HTTP/2 流错误
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
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-15`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像在 HTTP/2 协议层出现间歇性流错误（`Stream error in the HTTP/2 framing layer`），导致 `gcc-c++` RPM 包的两次下载尝试均失败，dnf 耗尽所有可用镜像后报错退出。

### 与 PR 变更的关联
**与 PR 无关。** 该 PR 仅新增了一个 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），其 `dnf install` 命令语法正确，所列包的名称和版本均有效。日志中 cmake-data 和 git-core 在遭遇同样的 HTTP/2 流错误后因重试成功而通过，表明失败是仓库镜像侧的网络协议问题，而非 PR 代码缺陷。`gcc-c++` 仅因恰好在该轮次未遇到成功的镜像而最终失败。

## 修复方向

### 方向 1（置信度: 中）
此失败为 CI 基础设施问题（openEuler 仓库镜像 HTTP/2 协议异常），与 PR 代码无关。建议：
- 直接**重试 CI**，观察同一构建是否能通过。
- 若持续复现，可考虑在 Dockerfile 的 `dnf install` 前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 将 dnf 降级为 HTTP/1.1，或切换至其他仓库镜像源（如 `repo.huaweicloud.com`）。

### 方向 2（置信度: 低）
如果 retry 后仍然失败且仅限于 `gcc-c++` 包，需确认该包的特定版本 `12.3.1-110.oe2403sp4` 在 openEuler 24.03-LTS-SP4 仓库中是否确实存在（非仓库协议问题，而是包本身缺失）。

## 需要进一步确认的点
1. **gcc-c++ 版本可用性**：确认 `gcc-c++-12.3.1-110.oe2403sp4` 在 `repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/x86_64/` 中的实际存在状态。
2. **仓库镜像健康状态**：openEuler 24.03-LTS-SP4 的 OS 仓库镜像是否近期存在 HTTP/2 协议层面的已知问题。
3. **同一镜像在其他 PR 中的表现**：近期其他使用 openEuler 24.03-lts-sp4 基础镜像的 PR 是否也出现类似 `Curl error (92)` 的 dnf 下载失败。
