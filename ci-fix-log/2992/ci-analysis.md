# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: HTTP/2 仓库下载流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `dnf install` 步骤）
- 失败原因: CI 构建环境通过 dnf 从 `repo.****.org`（openEuler 24.03-LTS-SP4 仓库）下载 RPM 包时，多个包（gcc-gfortran、glibc-devel、guile、gcc）遭遇 HTTP/2 流错误（Curl error 92），最终 gcc RPM 包因所有镜像均已尝试但均不成功而下载失败，导致 `dnf install` 返回 exit code 1。

### 与 PR 变更的关联
PR 新增了 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`，其 `dnf install` 步骤需要从 openEuler 24.03-LTS-SP4 仓库下载 gcc 等编译工具链和 openblas-devel、lapack-devel 库。Dockerfile 中 `dnf install` 安装的包名和语法均正确，失败原因不是 PR 代码错误，而是 openEuler 24.03-LTS-SP4 仓库镜像在构建时的 HTTP/2 连接不稳定，导致 RPM 包下载失败。该问题也同时影响了 stage-1 运行时阶段的 `dnf install`（#7），虽然 #7 部分包下载成功但最终因 #8 失败而被 CANCELED。

## 修复方向

### 方向 1（置信度: 中）
该失败很可能为临时性仓库网络问题。建议直接重新触发 CI 构建（rerun），若仓库服务已恢复则构建应能通过。无需修改 PR 代码。

### 方向 2（置信度: 低）
若多次重试仍失败，可在 Dockerfile 的 `dnf install` 命令前添加重试逻辑，或配置 dnf 使用备选镜像源。例如设置 `max_retries`、`retries` 等 dnf 重试参数，或添加 `--setopt=retries=10` 等选项提高下载成功率。

## 需要进一步确认的点
1. 确认 `repo.****.org` 在构建时间段是否存在已知服务中断或 HTTP/2 协议问题。
2. 确认相同仓库的其他 openEuler 24.03-LTS-SP4 镜像构建（如已有的 multiwfn cb37c53-oe2403sp3 或其他 SP4 镜像）在同期是否也出现相同的下载失败，以判断是否为仓库范围问题还是临时波动。
3. 如果仓库服务正常，需检查 CI runner 所在网络的代理或防火墙是否干扰了 HTTP/2 流量。

## 修复验证要求
无需代码修复，建议 rerun CI 验证。若 rerun 后仍失败，需获取仓库服务状态确认后再决定是否需要调整 Dockerfile 中的 dnf 配置。
