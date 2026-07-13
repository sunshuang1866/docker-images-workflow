# CI 失败分析报告

## 基本信息
- PR: #3120 — chore(cann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（附加匹配：模式20）
- 新模式标题: 构建节点磁盘耗尽
- 新模式症状关键词: no space left on device, ResourceExhausted, exporting layers, buildkit

## 根因分析

### 直接错误
```
#21 exporting to image
#21 exporting layers
#21 exporting layers 10.8s done
#21 ERROR: mount callback failed on /tmp/containerd-mount2709405373: mount callback failed on /tmp/containerd-mount2786893010: failed to write compressed diff: failed to create diff tar stream: failed to copy: /tmp/containerd-mount2786893010/usr/local/Ascend/ascend-toolkit/8.2.RC1.alpha002/opp/Ascend310/aicpu/Ascend310-aicpu_syskernels.tar.gz: write /var/lib/buildkit/runc-overlayfs/content/ingest/cf0921e8f9b68696f24e001212773e36efbcc15d9039658c3952c0c79be7f812/data: no space left on device
ERROR: failed to solve: ResourceExhausted: mount callback failed on /tmp/containerd-mount2709405373: mount callback failed on /tmp/containerd-mount2786893010: failed to write compressed diff: failed to create diff tar stream: failed to copy: /tmp/containerd-mount2786893010/usr/local/Ascend/ascend-toolkit/8.2.RC1.alpha002/opp/Ascend310/aicpu/Ascend310-aicpu_syskernels.tar.gz: write /var/lib/buildkit/runc-overlayfs/content/ingest/cf0921e8f9b68696f24e001212773e36efbcc15d9039658c3952c0c79be7f812/data: no space left on device
```

### 根因定位
- 失败位置: Docker 构建的第 #21 步 `exporting to image`
- 失败原因: CI 构建节点磁盘空间不足，BuildKit 在导出最终镜像层（compressed diff tar stream）时写入失败。CANN 工具包（含 opp、kernel、nnal 等组件）的安装目录体积巨大（数 GB），导出过程的临时文件耗尽了节点的可用磁盘空间。

### 与 PR 变更的关联
PR 新增了 `AI/cann/8.2.RC1.alpha002-python3.10/24.03-lts-sp4/Dockerfile`（180 行），引入了一个多阶段构建过程：编译 Python 3.10.17 源码 + 下载安装完整的 CANN 工具包、Kernels、NNAL 组件。所有 Dockerfile 构建步骤（#1 到 #20）均成功完成，包括 CANN 各组件的安装——在 `#21 exporting to image` 阶段 BuildKit 尝试将构建产物压缩为镜像层时因磁盘空间不足而失败。

**与 PR 代码错误无关**——Dockerfile 语法正确，所有 RUN 步骤均成功执行。失败纯粹是 CI 基础设施资源不足导致的。

附加关联（非根因）：日志中出现了 2 个 BuildKit `UndefinedVar` 警告：
```
2 warnings found (use docker --debug to expand):
 - UndefinedVar: Usage of undefined variable '$LD_LIBRARY_PATH' (line 108)
 - UndefinedVar: Usage of undefined variable '$PYTHONPATH' (line 111)
```
这匹配**模式20**（ENV 自引用未定义变量）。Dockerfile 第 108-111 行中 `ENV LD_LIBRARY_PATH=...:$LD_LIBRARY_PATH` 和 `ENV PYTHONPATH=...:$PYTHONPATH` 在首次定义时自引用了尚未存在的变量。这不是本次失败的直接原因，但应在修复时一并处理。

## 修复方向

### 方向 1（置信度: 高）
**CI 运维侧扩容**：增加 CI 构建节点的磁盘配额，或为 CANN 类大镜像分配专用的大容量构建节点。CANN 工具包完整安装后大小远超普通应用镜像，需保证 `/var/lib/buildkit` 所在分区有充足空间（建议至少 30-50GB 可用）。

### 方向 2（置信度: 中）
**Dockerfile 瘦身优化**：在当前 Dockerfile 中，Stage 2（cann-installer）内安装的 CANN 工具包包含大量非必需的 opp 内核文件（如 Ascend310 的 aicpu 固件包）。可尝试在安装完成后删除不需要的芯片平台目录（如 `Ascend310`、`Ascend910` 等非目标平台）来缩减镜像层大小，从而降低导出时的临时空间需求。

### 方向 3（置信度: 低）
**修正 UndefinedVar 警告**（模式20）：将 Dockerfile 中自引用未定义变量的 ENV 行改为使用 shell 默认值语法 `${VAR:-}`，消除 BuildKit 警告。虽然不解决本次 disk 问题，但可提升构建质量。

## 需要进一步确认的点
1. CI 构建节点的磁盘默认配额是多少，是否需要申请工作流级别的扩容
2. 该仓库历史中是否存在其他大镜像（如完整 AI 框架镜像）遇到同类磁盘不足问题，是否有现成的扩容流程
3. 上游 CANN 工具包的安装后实际磁盘占用大小（可据此评估最小所需磁盘配额）
4. 是否可以跳过 Ascend310（推理芯片）相关的 opp 内核安装以减少镜像体积（需确认目标使用场景）

## 修复验证要求
由于根因为 infra-error（磁盘耗尽），Code Fixer 无需修改代码。若选择方向 2（Dockerfile 瘦身），需在本地或扩容后的 CI 环境验证：重新触发 Docker 构建，确认 `exporting layers` 不再报 `no space left on device` 错误。
