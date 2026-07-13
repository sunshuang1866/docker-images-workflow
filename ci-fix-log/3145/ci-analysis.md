# CI 失败分析报告

## 基本信息
- PR: #3145 — chore(text-generation-inference-cpu): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 手动中止构建（含替代方案配置异常）
- 新模式症状关键词: `Aborted by`, `failed to link`, `update-alternatives`, `exists and it is not a symlink`, `Canceled: context canceled`

## 根因分析

### 直接错误
```
Build was aborted
Aborted by 闫志聪
#44 CANCELED
ERROR: failed to solve: Canceled: context canceled
Finished: ABORTED
```

构建被用户"闫志聪"手动中止，并非代码级错误导致构建自然失败。中止时构建正在进行 intel-extension-for-pytorch 的 C++ 源码编译（进度约 66%）。

### 非致命但值得关注的错误

**1. update-alternatives 安装失败**（#27、#28、#31、#32）：
```
#27 0.093 failed to link /usr/bin/g++ -> /etc/alternatives/g++: /usr/bin/g++ exists and it is not a symlink
#28 0.060 failed to link /usr/bin/gcc -> /etc/alternatives/gcc: /usr/bin/gcc exists and it is not a symlink
#31 0.056 failed to link /usr/bin/c++ -> /etc/alternatives/c++: /usr/bin/c++ exists and it is not a symlink
#32 0.055 failed to link /usr/bin/c++ -> /etc/alternatives/c++: /usr/bin/c++ exists and it is not a symlink
```

**2. Yum 镜像站网络错误**（#10，重试后恢复）：
```
[MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer
[MIRROR] libstdc++-devel-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92)
[MIRROR] perl-Math-BigInt-2.0030.02-1.oe2403sp4.noarch.rpm: Curl error (56): Failure when receiving data from the peer
```

**3. Conda 依赖解析失败**（#35、#36，自动回退后继续）：
```
#35 36.18 Solving environment: ...working... failed with initial frozen solve. Retrying with flexible solve.
#36 33.10 failed with initial frozen solve. Retrying with flexible solve.
```

**4. BuildKit ENV 格式弃用警告**：
```
- LegacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format (line 93)
```

### 根因定位
- 失败位置: 不适用（构建被手动中止，非代码级错误位置）
- 失败原因: 构建过程耗时过长（intel-extension-for-pytorch 全量从源码编译），被运维人员手动取消

### 与 PR 变更的关联
PR 新增了一个完整的 Dockerfile（165 行）用于 openEuler 24.03-LTS-SP4。Dockerfile 本身可能存在的潜在问题：

1. **update-alternatives 与 SP4 基础镜像不兼容**：Dockerfile 在 `yum install gcc g++` 后使用 `update-alternatives --install` 尝试将 `/usr/bin/gcc`、`/usr/bin/g++`、`/usr/bin/c++` 注册为 alternatives 管理的 symlink，但 openEuler 24.03-LTS-SP4 基础镜像（或 yum 安装的 gcc/g++ 包）直接将二进制文件安装在 `/usr/bin/` 下作为普通文件，导致 `--install` 操作失败。虽然 `update-alternatives` 对此类场景返回非致命信息而非错误退出码（构建继续执行），但如果后续步骤依赖 alternatives 管理的符号链接（如通过 `--set` 切换版本），实际设置可能未生效。

2. **ENV 格式问题**：第 93 行附近（估计为 `ENV LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/opt/conda/lib/"`）使用了 `ENV key value` 格式（空格分隔+引号），BuildKit 建议改为 `ENV key=value` 格式（等号分隔）。

## 修复方向

### 方向 1（置信度: 高）
**处理 update-alternatives 冲突**：在 SP4 基础镜像中，`yum install gcc g++` 安装后的二进制文件直接位于 `/usr/bin/` 下而非通过 alternatives 管理。需确认 SP4 中 gcc-12 是否已经是默认编译器（`/usr/bin/gcc` 是否本身就是 gcc-12）。若是，可直接移除全部 `update-alternatives --install` 和 `--set` 行；若需要显式指定编译器版本，需先移除已存在的普通文件（`rm /usr/bin/gcc /usr/bin/g++ /usr/bin/c++ /usr/bin/cc`）再执行 alternatives 注册。

### 方向 2（置信度: 中）
**优化构建耗时**：intel-extension-for-pytorch 从源码全量编译极度耗时，可能是被手动中止的根本原因。如果这是 CI 超时策略下的必然结果，考虑以下优化：
- 减少并行编译 job 数（可能因资源争抢导致整体缓慢）
- 确认 SP4 是否必须编译 intel-extension-for-pytorch，或其他平台（如 24.03-lts）已有相同版本的构建缓存

### 方向 3（置信度: 低）
**修复 ENV 格式警告**：将第 93 行的 `ENV LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/opt/conda/lib/"` 改为 `ENV LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/conda/lib/"` 并使用等号格式，消除 BuildKit 警告。

## 需要进一步确认的点
1. **实际中止原因**：需与用户"闫志聪"确认手动中止的具体原因——是构建超时、观察到错误、还是误操作。如果是因为 CI 平台有硬性超时限制，则需确认超时阈值及 intel-extension-for-pytorch 编译的预期时间。
2. **SP4 基础镜像中 gcc/g++ 的实际安装方式**：需在 openEuler 24.03-LTS-SP4 容器中确认 `yum install gcc g++` 后 `/usr/bin/gcc` 是否为普通文件而非 symlink，以及默认 gcc 版本是否为 gcc-12。这将决定 update-alternatives 命令是否需要、如何修改。
3. **SP4 与 SP3 版本的同源 Dockerfile 对比**：查看 `AI/text-generation-inference-cpu/2.4.0/24.03-lts/Dockerfile`（若存在）中的 gcc 管理方式，判断 SP4 版本的差异是预期内调整还是移植错误。
4. **Conda 依赖解析失败的影响**：虽然 conda 回退到 flexible solve 后构建继续，需确认最终安装的 gperftools/mkl 版本是否正确，是否会导致后续编译或运行时问题。
5. **Yum 镜像站可用性**：SP4 的 repo 镜像站是否稳定，Curl HTTP/2 错误是否频繁发生。

## 修复验证要求
若修复方向 1 涉及移除或修改 update-alternatives 命令，code-fixer 必须：
- 在 `openeuler/openeuler:24.03-lts-sp4` 容器中执行 `yum install -y gcc g++` 后，运行 `ls -la /usr/bin/gcc /usr/bin/g++ /usr/bin/c++ /usr/bin/cc` 确认这些路径是普通文件还是 symlink。
- 运行 `gcc --version` 和 `g++ --version` 确认默认编译器版本。
- 验证修改后的 Dockerfile 的 update-alternatives 步骤能正确执行（不出 `failed to link` 错误）或确认移除后编译器行为正确。
