# CI 失败分析报告

## 基本信息
- PR: #2743 — 【自动升级】seissol容器镜像升级至202103.Sumatra版本.
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 模式22 (部分匹配: 同一类 git clone ref 不存在错误) + 模式20 (附加发现: ENV 自引用未定义变量)
- 新模式标题: -
- 新模式症状关键词: -

## 根因分析

### 直接错误
```
#14 0.067 Cloning into '/tmp/seissol'...
#14 0.681 warning: Could not find remote branch v202103.Sumatra to clone.
#14 0.681 fatal: Remote branch v202103.Sumatra not found in upstream origin
#14 ERROR: process "/bin/sh -c git clone --recursive --depth 1 --branch v${VERSION} https://github.com/SeisSol/SeisSol.git /tmp/seissol && ..." did not complete successfully: exit code: 128
------
ERROR: failed to solve: process "..." did not complete successfully: exit code: 128
```

### 根因定位
- 失败位置: `HPC/seissol/202103.Sumatra/24.03-lts-sp3/Dockerfile:59`
- 失败原因: Dockerfile 中 `git clone --branch v${VERSION}`（展开为 `--branch v202103.Sumatra`）指定的远程 ref 在上游 SeisSol/SeisSol 仓库中不存在，导致 git clone 返回 exit code 128。其余构建步骤（Eigen、eASI、GKlib、METIS、ParMETIS）均成功通过。

### 与 PR 变更的关联
PR 新增了完整的 SeisSol Dockerfile（99 行），其中第 4 行定义 `ARG VERSION=202103.Sumatra`，第 59 行使用 `--branch v${VERSION}` 构造 git clone 命令。该 Dockerfile 为首次引入，失败完全由本次 PR 的变更直接触发。

## 修复方向

### 方向 1（置信度: 中）
**确认上游 SeisSol 仓库中 `v202103.Sumatra` 标签的实际名称。**
- 若标签存在但 `--depth 1` 导致无法解析：将克隆流程改为先浅克隆再按标签 checkout，或移除 `--depth 1` 改为完整克隆。
- 若标签名称不是 `v202103.Sumatra`（例如不带 `v` 前缀，或其他格式）：修正 Dockerfile 中 `--branch` 的参数，使其与上游实际标签名匹配。

### 方向 2（置信度: 高，属于附加发现，非本次失败根因）
**修复 `$LD_LIBRARY_PATH` 未定义变量警告（模式20）。**
Dockerfile 第 96 行 `ENV LD_LIBRARY_PATH=/usr/lib64/openmpi/lib:/usr/local/lib64:/usr/local/lib:$LD_LIBRARY_PATH` 在运行时阶段（第二个 FROM）自引用了尚未定义的变量，BuildKit 产生 `UndefinedVar` 警告。虽然此警告不直接导致本次构建失败，但应在修复主要问题时一并处理。将 `$LD_LIBRARY_PATH` 改为 `${LD_LIBRARY_PATH:-}` 即可消除警告。

## 需要进一步确认的点
1. 在 SeisSol/SeisSol GitHub 仓库中确认标签 `v202103.Sumatra` 是否存在，以及其精确格式（访问 https://github.com/SeisSol/SeisSol/tags）
2. 若标签存在但 clone 失败，需验证是否为 `--depth 1` 浅克隆无法解析标签 ref 的问题（通常发生在较旧版本的 Git 服务端）
3. 确认运行时阶段的 `LD_LIBRARY_PATH` 是否需要继承 builder 阶段的路径，还是仅需要 `/usr/lib64/openmpi/lib:/usr/local/lib64:/usr/local/lib`

## 修复验证要求
code-fixer 必须从 SeisSol 上游仓库（https://github.com/SeisSol/SeisSol）确认 `v202103.Sumatra` 的实际标签名称，并使用确认后的标签名在本地验证 `git clone --branch <correct_tag> https://github.com/SeisSol/SeisSol.git` 能正常克隆后再提交修改。
