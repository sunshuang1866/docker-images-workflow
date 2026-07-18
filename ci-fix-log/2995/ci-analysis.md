# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, /bin/sh^M, bwa_test.sh, No such file or directory

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI 基础设施脚本 `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`（由 eulerpublisher 包提供）
- 失败原因: CI 工具 `eulerpublisher` 内置的 `bwa_test.sh` 测试脚本使用了 Windows 风格行尾（CRLF，即 `\r\n`），导致 shebang 行 `#!/bin/sh` 被解析为 `#!/bin/sh\r`，系统尝试寻找名为 `/bin/sh\r` 的解释器失败，报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联
**与 PR 无关。** 本次失败是 CI 基础设施问题，非 PR 代码变更触发：

1. PR 的所有新增/修改文件（Dockerfile、README.md、image-info.yml、meta.yml）均不含 CRLF 行尾或测试脚本。
2. Docker 镜像构建和推送阶段**全部成功**——`yum install`、源码下载、`make` 编译、构建产物导出、镜像推送均无错误。
3. 失败发生在镜像推送完成后的 `[Check]` 阶段，由 `eulerpublisher` 工具调用其自身的 `bwa_test.sh` 测试脚本时触发。该脚本属于 CI 流水线基础设施（`/usr/etc/eulerpublisher/tests/container/app/`），与 PR 代码无任何关系。
4. 日志末尾明确显示 `Finished: FAILURE`，失败点唯一且清晰指向 `bad interpreter` 行尾问题。

## 修复方向

### 方向 1（置信度: 高）
CI 流水线维护方需修复 `eulerpublisher` 包中的 `bwa_test.sh` 测试脚本，将其行尾从 Windows 格式（CRLF）转换为 Unix 格式（LF）。可以在脚本部署阶段执行 `dos2unix` 或 `sed -i 's/\r$//'` 对测试脚本目录进行批量转换，或修复脚本的源文件确保以 LF 格式提交到版本控制。

**注意：此修复不在 Code Fixer 负责范围内，属于 CI 基础设施维护任务。**

## 需要进一步确认的点
- 确认 `eulerpublisher` 包中其他以 `_test.sh` 结尾的测试脚本是否同样存在 CRLF 行尾问题（如 `HPC/`、`AI/` 等场景的测试脚本），避免其他镜像的 Check 阶段出现同类失败。
- 确认 `bwa_test.sh` 的来源——是 eulerpublisher 包自有文件还是从某 git 仓库动态拉取的，以便从根本上修正源文件的行尾格式。
