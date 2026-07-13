# CI 失败分析报告

## 基本信息
- PR: #2983 — chore(fbthrift): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 构建超时/OOM 被杀
- 新模式症状关键词: ChannelClosedException, EOFException, fatal: command execution failed, Unexpected termination of the channel, ecs-build-docker-x86-hk

## 根因分析

### 直接错误
```
#11 2130.5 Writing cargo config for fbthrift to /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/build/fbthrift/source/thrift/lib/rust/.cargo/config.toml
FATAL: command execution failed
java.io.EOFException
Caused: java.io.IOException: Unexpected termination of the channel
Caused: hudson.remoting.ChannelClosedException: Channel "hudson.remoting.Channel@24d4cc0d:ecs-build-docker-x86-hk": Remote call on ecs-build-docker-x86-hk failed. The channel is closing down or has closed down
FATAL: Unable to delete script file /tmp/jenkins3161304096436833533.sh
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: Dockerfile:18（`RUN git clone ... && ./getdeps.py build fbthrift` 步骤）的 Docker 构建过程中
- 失败原因: Docker 构建在耗时约 35 分钟、执行到 fetcher 依赖解析/准备阶段（Writing cargo config）时，Jenkins runner 上的 shell 进程被异常终止，导致 Channel 关闭，整个 Build 被标记为失败。日志中**未出现任何编译错误、依赖缺失或代码层面的错误**，构建输出在终止前进展正常（boost 头文件拷贝→依赖 folly/fizz/mvfst/wangle 版本锁定→cargo config 写入）。结合执行耗时（2130+ 秒）和进程被外部杀掉的特征，根因极可能是 **CI runner 超时（Jenkins job timeout）或 OOM Killer 杀死了 docker build 进程**。

### 与 PR 变更的关联
- **PR 直接触发了构建资源需求激增**。该 PR 新增了 openEuler 24.03-LTS-SP4 上 fbthrift 的 Dockerfile，其构建方式为通过 `getdeps.py` 从源码编译 fbthrift 及其全部 C++ 依赖（boost、folly、fizz、mvfst、wangle 等），这是一个极其重量级的构建（仅依赖 fetch/解析就用了 35+ 分钟，完整编译可能需要数小时）。
- 对比已有的 `24.03-lts-sp3` Dockerfile（同仓库同项目的其他版本），如果旧版本构建时间本就接近超时阈值，新增一个相同量级的构建任务可能恰好触发 runner 的超时/OOM 限制。
- `fix_getdeps.py` 中的正则 patch（`r'def _verify_hash\(self[^)]*\)[^:]*:.*?(?=\n    def )'`）如果未能正确匹配上游 `fetcher.py` 中的 `_verify_hash` 方法签名，patch 将静默失效（原方法保留），但日志在进入实际编译阶段之前就已终止，无法确认该 patch 是否成功执行。

## 修复方向

### 方向 1（置信度: 中）
**构建超时/OOM → 延长 CI timeout 或增加 runner 资源**

检查 Jenkins job 的超时配置和 runner 的内存上限。fbthrift 的 getdeps 全量源码构建在 2C/4G 的 runner 上执行 35+ 分钟仍未进入实际编译阶段，completion 可能需要 > 2 小时。建议增大 runner 规格（内存至少 8G，最好 16G）或将 job timeout 设置为 4 小时以上。

### 方向 2（置信度: 低）
**fix_getdeps.py 正则未匹配导致 hash 校验失败（预防性）**

`fix_getdeps.py` 第 2 步的正则 `r'def _verify_hash\(self[^)]*\)[^:]*:.*?(?=\n    def )'` 用于替换 `fetcher.py` 中的 `_verify_hash` 方法体。如果 fbthrift v2026.06.22.00 对应的 fetcher.py 中 `_verify_hash` 的实际签名与此正则不匹配（例如参数模式不同，或 Python 方法换行风格不一致），replace 会静默无操作，后续 libaio 的哈希校验将失败——但本次日志未到达该阶段，无法确认。建议在 runner 资源充足的前提下重试，以观察是否出现后续的 hash mismatch 错误。

### 方向 3（置信度: 低）
**使用 --allow-system-packages 但 getdeps 仍从源码构建 boost**

Dockerfile 中安装了 `boost-devel` 并通过 `--allow-system-packages` 期望使用系统 boost，但日志显示 getdeps 仍在解压和安装 boost_1_83_0（从 `#11 525.*` 的大量 boost 头文件复制可见）。这意味着 `--allow-system-packages` 未能成功跳过 boost 的源码构建，显著增加了构建时间和资源消耗。可检查是否需额外的 getdeps 参数或 manifest 配置来真正使用系统包。

## 需要进一步确认的点

1. **Jenkins job 超时配置**：当前 job 的 timeout 是多少？2100+ 秒（35 分钟）是否是触发阈值？
2. **Runner 规格**：`ecs-build-docker-x86-hk` 节点的内存和 CPU 配置？是否需要升级到更大规格？
3. **SP3 版本构建时间**：已有的 `24.03-lts-sp3` 的 fbthrift Dockerfile 构建是否使用了不同的优化策略（如预编译二进制包、多阶段构建）使其在 CI 中能成功？如果 SP3 也使用相同的 getdeps 全量编译方式且能成功，则本次失败更有可能是 runner 节点偶发问题而非超时。
4. **fix_getdeps.py 正则验证**：需从 fbthrift v2026.06.22.00 的上游仓库获取 `build/fbcode_builder/getdeps/fetcher.py`，验证 `_verify_hash` 方法的实际签名是否与之正则匹配。若未匹配，即使解决超时问题后仍会出现 libaio hash 校验失败。
5. **是否 OOM**：检查 Jenkins 节点的 dmesg/kernel log 中是否有 `Out of memory` 或 `oom-killer` 记录，以确认是 OOM 而非 timeout。
