# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error, HTTP/2 framing layer, INTERNAL_ERROR, dnf install, No more mirrors to try

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`:6（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像在 HTTP/2 协议层面返回流错误（Curl error 92），导致 `cmake-data`、`git-core`、`gcc-c++` 三个 RPM 包下载失败。其中 `cmake-data` 和 `git-core` 在切换镜像后重试成功，但 `gcc-c++` 重试两次后仍失败，dnf 耗尽了所有可用镜像（"No more mirrors to try"），整个 `dnf install` 命令以 exit code 1 失败。

### 与 PR 变更的关联
PR 新增了 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`，其中包含 `dnf install -y` 命令安装大量编译依赖。失败发生在 PR 新增的这行 `RUN` 指令上，但**与 PR 代码改动本身无关**——`dnf install` 命令的包名列表和语法均正确（仓库元数据已成功下载，事务摘要显示 258 个包安装计划正常生成），失败是 openEuler 官方仓库镜像的网络/协议层瞬时故障导致的。

## 修复方向

### 方向 1（置信度: 中）
**重试 CI 构建**。这是一个 transient infra-error，openEuler 仓库镜像在 CI 运行期间 HTTP/2 服务不稳定，重新触发构建大概率可以成功，无需修改任何代码。

### 方向 2（置信度: 低）
如果多次重试后同一个包（`gcc-c++`）始终失败，可能是 `repo.****.org` 上该 RPM 文件本身存在问题（如文件损坏、校验和不匹配等）。此时需要确认上游仓库镜像中该文件是否完整可用，或等待镜像站修复。

## 需要进一步确认的点
1. 该 CI 失败是否仅在单次运行中出现（瞬态网络问题），还是在多次重试中持续复现？如果重试后构建成功，则可确认是 infra-error。
2. openEuler 24.03-LTS-SP4 仓库镜像 `repo.****.org` 在构建时段是否有已知的 HTTP/2 服务不稳定问题？
3. 如果该错误在多次重试中持续复现，需要检查上游镜像站上 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 文件本身是否损坏或不存在。
