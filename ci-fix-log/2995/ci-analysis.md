# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 测试脚本行尾符错误
- 新模式症状关键词: `^M: bad interpreter`, `No such file or directory`, `/bin/sh^M`, `bwa_test.sh`

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施测试脚本，非 PR 文件）
- 失败原因: CI 基础设施 `eulerpublisher` 包中的 `bwa_test.sh` 测试脚本使用了 Windows 风格行尾符（CRLF），导致 shebang 行 `#!/bin/sh` 末尾附带回车符 `\r`（显示为 `^M`），内核无法找到名为 `/bin/sh\r` 的解释器，报 "bad interpreter: No such file or directory"。

### 与 PR 变更的关联
**PR 变更与此失败无直接关系。** 证据如下：
1. Docker 镜像构建阶段（`#7 [2/2] RUN yum -y install ...`）**完全成功**——所有编译、安装、清理步骤均无错误退出，最终成功 `exporting to image` 并 `pushing manifest`。
2. 失败发生在 CI 流水线的 `[Check]` 阶段，即镜像构建和推送完成后，由 `eulerpublisher` 包执行镜像功能验证测试（`bwa_test.sh`）时触发。
3. 报错的 `bwa_test.sh` 位于 CI runner 上已安装的 `eulerpublisher` Python 包路径（`/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/`）中，**不属于此 PR 的文件变更范围**。PR 的 diff 仅包含 Dockerfile、README.md、image-info.yml、meta.yml 四个文件。
4. PR 新增的 Dockerfile 自身无任何行尾符问题（构建阶段能正常执行所有 Shell 命令即可证明）。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施 `eulerpublisher` 仓库中的 `tests/container/app/bwa_test.sh` 文件需要转换为 Unix 行尾符（LF）。执行 `dos2unix` 或在编辑器中保存为 Unix 格式后重新提交到 `eulerpublisher` 仓库即可。

### 方向 2（置信度: 低）
若 `bwa_test.sh` 在 `eulerpublisher` 仓库中原本是正确的 LF 格式，但在 CI 流程中被某一步骤（如代码检出、文件传输）意外转换了行尾符，则需要检查 CI 流程中的文件传输或拷贝步骤是否引入了 CRLF 转换。

## 需要进一步确认的点
1. 确认 `eulerpublisher` 仓库中 `tests/container/app/bwa_test.sh` 的**当前行尾符格式**：用 `file` 命令或 `cat -v` 查看是否真的是 CRLF。
2. 确认该测试脚本是**新近添加**（配合 openEuler 24.03-LTS-SP4 支持）还是**已存在但因某种原因才暴露问题**——如果 bwa 的 22.03-lts-sp3 变体之前也能通过同一测试脚本的 Check 阶段，则需调查为什么同一个 `bwa_test.sh` 之前可以执行而现在不行。
3. 检查 `eulerpublisher` 仓库的 `.gitattributes` 配置是否正确，确认未对 `*.sh` 文件启用 `eol=crlf` 或 `text=auto` 导致的自动转换。

## 修复验证要求
此失败属于 CI 基础设施问题（infra-error），修复需在 `eulerpublisher` 仓库侧进行。Code Fixer 无需对 PR #2995 的代码进行任何修改。验证方法：
- 修复 `bwa_test.sh` 的行尾符后，重新触发 CI 流水线，确认 `[Check]` 阶段正常通过即可。
