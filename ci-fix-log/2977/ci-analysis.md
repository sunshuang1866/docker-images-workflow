# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, yum install, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（yum install 步骤）
- 失败原因: `repo.openeuler.org` 仓库在 aarch64 构建过程中出现多次 HTTP/2 流错误（Curl error 92, INTERNAL_ERROR），yum 的自动重试机制让前 3 次失败（gcc、kernel-headers、perl-MIME-Base64）最终成功下载，但第 4 次（vim-common）重试耗尽，导致 `yum install` 整体失败。

### 与 PR 变更的关联
PR 新增了 `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`，其 yum install 步骤本身语法正确、依赖声明完整。失败与 PR 代码变更无关，完全由 `repo.openeuler.org` 软件源的瞬时网络故障导致。该仓库在约 21 分钟的下载过程中出现了至少 4 次 HTTP/2 协议层面的流中断，其中 3 次被 yum 自动恢复，1 次（最后一个包 vim-common，包序号 173/173）耗尽重试次数而失败。

## 修复方向

### 方向 1（置信度: 高）
这是 openEuler 官方仓库 `repo.openeuler.org` 的瞬时基础设施问题（HTTP/2 连接不稳定），Dockerfile 本身无需修改。建议等待仓库恢复后重新触发 CI 构建。若问题持续出现，可考虑在 Dockerfile 的 yum install 步骤前添加重试逻辑（如 `yum install -y ... || yum install -y ...`）或在 yum 配置中增加 `retries` 和 `timeout` 参数。

## 需要进一步确认的点
- 确认该失败是偶发（单次网络抖动）还是持续性问题：检查同一时间段其他 PR 的 aarch64 构建是否也出现类似 `Curl error (92)` 或 `HTTP/2 framing layer` 错误
- 确认 x86_64 架构的同 PR 构建是否成功（当前日志仅包含 aarch64 runner 的输出）——若 x86_64 成功而 aarch64 持续失败，则可能存在 aarch64 构建节点到 `repo.openeuler.org` 的网络链路问题
