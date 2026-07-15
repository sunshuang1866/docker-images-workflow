# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI Check 阶段，执行 `bwa_test.sh` 测试脚本时
- 失败原因: `eulerpublisher` CI 工具中 `bwa_test.sh` 测试脚本的 shebang 行（`#!/bin/sh`）末尾携带 Windows 换行符 `\r`（CRLF），导致系统将解释器路径误读为 `/bin/sh\r`，报 `bad interpreter: No such file or directory`

### Docker 构建与推送均成功
日志显示镜像构建（`#7 DONE 199.0s`）、导出（`#8 DONE 8.4s`）、推送全部正常完成：
- `[Build] finished`
- `[Push] finished`
- 失败仅发生在最后的 `[Check]` 阶段

### 与 PR 变更的关联
**与 PR 无关**。PR 变更仅涉及以下文件，均不包含测试脚本：
- `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（新增，19 行，Docker 构建步骤）
- `HPC/bwa/README.md`（新增 1 行标签说明）
- `HPC/bwa/doc/image-info.yml`（新增 1 行镜像条目）
- `HPC/bwa/meta.yml`（新增 3 行版本映射）

出错的 `bwa_test.sh` 位于 `/usr/etc/eulerpublisher/tests/container/app/`（由 pip 安装的 eulerpublisher 包或 CI 执行环境提供），与 PR 代码无关。该脚本自身的行尾格式（CRLF vs LF）问题属于 CI 基础设施配置或 eulerpublisher 发布物损坏。

## 修复方向

### 方向 1（置信度: 中）
在 eulerpublisher 仓库或 CI runner 环境中，将 `bwa_test.sh` 的行尾从 CRLF 转换为 LF（`dos2unix` 或 `sed -i 's/\r$//'`）。这需要在发布 eulerpublisher 包的流程中修复，或在 CI 执行测试前对脚本做格式归一化。

### 方向 2（置信度: 低）
若此问题仅在特定 CI runner 上出现（如 git clone 时 `core.autocrlf=true` 导致 checked-out 文件被自动转换为 CRLF），则需排查该 runner 的 git 全局配置。

## 需要进一步确认的点
1. `bwa_test.sh` 在 eulerpublisher 仓库源码中的实际行尾格式（LF 还是 CRLF）
2. 同一 CI 环境中，其他应用镜像（非 bwa）的 Check 阶段是否有相同 `^M` 错误，以判断是全局问题还是仅 bwa_test.sh 文件损坏
3. 该 CI runner 的 git `core.autocrlf` 配置值
4. 若为首次构建 bwa SP4 触发的路径——确认之前的 bwa SP3 构建在同一 CI 环境下是否通过 Check 阶段

## 修复验证要求
无需验证。此失败为 CI 基础设施错误（infra-error），不属于 Code Fixer 修复范围。PR 中的 Dockerfile 构建逻辑本身没有问题。
