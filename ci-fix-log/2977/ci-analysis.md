# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler 仓库 HTTP/2 协议错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, repo.openeuler.org, aarch64

## 根因分析

### 直接错误
```
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

日志中同时出现了多个包的 HTTP/2 错误（均来自 `repo.openeuler.org` aarch64 仓库）：
- `#7 556.2` gcc — Curl error (92)，重试后成功（#7 831.9）
- `#7 836.2` kernel-headers — Curl error (92)，重试后成功（#7 855.7）
- `#7 1029.3` perl-MIME-Base64 — Curl error (56)，重试后成功（#7 1030.5）
- `#7 1310.2` vim-common — Curl error (92)，**重试全部失败**

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的官方仓库 `repo.openeuler.org` 在服务端 HTTP/2 层存在协议错误（HTTP/2 stream 非正常关闭，Curl error 92: INTERNAL_ERROR），导致 aarch64 架构下 `vim-common` 包的下载在所有镜像源重试后仍然失败

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了一个 Dockerfile 和三个文档/元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中 `yum install` 命令语法正确，包名列表与同仓库其他 SP4 版 Dockerfile（如 sp3 版本）一致。失败原因是 openEuler 官方包仓库的服务端基础设施问题——HTTP/2 连接在传输过程中被服务端非正常关闭，且重试机制未能覆盖该场景。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复**。此为 openEuler 官方仓库 `repo.openeuler.org` 的服务端网络/协议层临时故障（HTTP/2 stream INTERNAL_ERROR），与 PR 提交的 Dockerfile 内容无关。应触发 CI 重跑（retry），等待仓库服务恢复正常。若持续失败，应由 CI 基础设施团队联系 openEuler 仓库运维排查 HTTP/2 服务端配置。

### 方向 2（置信度: 低）
若短期内仓库问题无法解决，可在 Dockerfile 中为 `yum install` 添加重试逻辑（如 `yum install --retries 5` 或循环重试），但这属于网络容错性优化而非根因修复，且不能保证解决 HTTP/2 协议层错误。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 aarch64 仓库在 CI 失败时间点是否存在 HTTP/2 服务端问题（检查仓库健康状态）
- 确认同一时间其他依赖 `repo.openeuler.org` 的 CI job 是否也出现类似的 HTTP/2 流错误
- 确认 `vim-common` 包（2:9.0.2092-36.oe2403sp4）在该仓库中是否正常可下载（验证 SHA256 / 手动 wget 测试）
