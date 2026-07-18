# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: "DNF镜像HTTP/2协议错误"
- 新模式症状关键词: "Curl error (92), HTTP/2 stream, INTERNAL_ERROR, Stream error in the HTTP/2 framing layer, No more mirrors to try"

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 DNF 仓库镜像在 HTTP/2 协议层面存在不稳定性，3 个 RPM 包（cmake-data、git-core、gcc-c++）的下载过程中均出现 `Curl error (92): Stream error in the HTTP/2 framing layer`。其中 cmake-data 和 git-core 重试后下载成功，但 gcc-c++（13 MB）两次尝试（stream 65 和 stream 83）均失败，DNF 耗尽所有已尝试的镜像后放弃，导致整个 `dnf install` 步骤退出码为 1。

### 与 PR 变更的关联
**与 PR 代码变更无关**。PR 仅新增了一个全新的 Dockerfile（`Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`）以及配套的 README、image-info.yml、meta.yml 更新。Dockerfile 中的 `dnf install` 命令语法正确，所列软件包名称均有效（DNF 成功解析了 258 个依赖包和 914 MB 总下载量）。失败纯粹是 openEuler 官方仓库镜像在构建期间的 HTTP/2 协议不稳定所致，属于临时性基础设施故障。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试（retrigger CI）**。此为典型的临时性网络/镜像故障（HTTP/2 stream INTERNAL_ERROR），Dockerfile 代码本身无问题。在 openEuler 仓库镜像恢复稳定后重新触发 CI 构建即可通过。

### 方向 2（置信度: 低，仅当问题持续复现时考虑）
若多次重试后仍持续失败，说明 openEuler 24.03-LTS-SP4 仓库的特定镜像节点存在持久性问题。此时可考虑在 Dockerfile 的 `dnf install` 前增加 `RUN dnf makecache --refresh` 或尝试指定备用镜像源（如替换 `/etc/yum.repos.d/` 中的 baseurl 为其他已知可用的 mirror），但无证据表明目前需要此步骤。

## 需要进一步确认的点
- 该 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 协议问题是否为已知故障（可查阅 openEuler Infra 侧是否有相关公告）
- 若此 PR 其他受影响的下游架构 job（如 aarch64 构建）也失败，需确认是否为同类型错误（本报告仅基于 x86_64 构建日志）

## 修复验证要求
无需代码修复，直接重新触发 CI 构建即可验证。若重试后仍失败，需获取多次失败的一致错误模式后再做判断。
