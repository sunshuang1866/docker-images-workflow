# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: SP4 仓库 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在下载 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 等包时反复出现 HTTP/2 协议流错误（Curl error 92: Stream error in the HTTP/2 framing layer），所有已配置的镜像源均尝试失败，dnf 放弃下载并报错退出。构建器阶段（#8）和运行时阶段（#7）均受波及，其中构建器阶段因 `gcc` 包下载彻底失败而中止，导致运行时阶段被联动取消（CANCELED）。

### 与 PR 变更的关联
PR 变更与失败**无直接因果关系**。PR 仅新增了一个结构正确、语法无误的 Dockerfile（与现有 SP3 版本同构），以及配套的元数据文件更新（README.md、image-info.yml、meta.yml）。失败根因是 CI 构建环境中 openEuler 24.03-LTS-SP4 RPM 仓库服务器的 HTTP/2 协议层存在间歇性故障，与 PR 的代码变更无关。该 Dockerfile 本身逻辑正确，依赖声明完整。

## 修复方向

### 方向 1（置信度: 低）
**重试触发 CI**。由于错误类型为 `infra-error`（RPM 仓库 HTTP/2 服务器端流错误），属于偶发性网络基础设施问题，无需修改任何代码。等待仓库服务恢复后重新触发 CI 构建即可。若多次重试持续失败，则需排查 openEuler 24.03-LTS-SP4 仓库服务健康状态。

### 方向 2（置信度: 低）
**降低 dnf 的 HTTP 协议版本**。若 SP4 仓库对 HTTP/2 支持不稳定，可在 Dockerfile 的 `dnf install` 前为 curl/libcurl 禁用 HTTP/2 协商（如设置 `--http1.1` 选项或配置 `http2=false` in dnf.conf），回退到 HTTP/1.1 规避协议层错误。但此方案仅为临时绕过，不解决服务端根因，且需确认 dnf 支持该配置。

## 需要进一步确认的点
1. openEuler 24.03-LTS-SP4 RPM 仓库（`repo.****.org` 对应的实际镜像站）当前服务健康状态——是否仅有 HTTP/2 故障，HTTP/1.1 能否正常下载。
2. 同一时间窗口内其他使用 SP4 基础镜像的 CI 构建是否也出现相同错误，以确认是否为单次偶发还是持续性故障。
3. 日志中 `repo.****.org` 地址被脱敏，需确认实际仓库地址以判断是官方仓库还是内部镜像源。
4. 失败日志仅包含 x86_64 架构的构建信息，aarch64 架构的构建结果未知（可能成功、也可能同样失败），需要确认 arm64 runner 的日志。
