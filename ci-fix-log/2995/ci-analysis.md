# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾符
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bwa_test.sh, /bin/sh

## 根因分析

### 直接错误
```
#7 DONE 199.0s
#8 DONE 8.4s
2026-07-10 11:58:05,860 - INFO - [Build] finished
2026-07-10 11:58:05,860 - INFO - [Push] finished
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI 基础设施的测试脚本 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（即 `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`）
- 失败原因: CI 编排工具 `eulerpublisher` 中的测试脚本 `bwa_test.sh` 包含 Windows 风格行尾符（CRLF，即 `\r\n`），导致 shebang 被解析为 `/bin/sh\r`（带回车字符），系统找不到该解释器，报 `bad interpreter: No such file or directory`

### 与 PR 变更的关联
**与 PR 变更无关。** PR #2995 仅修改了 4 个文件：
1. `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（新增）— Docker 构建成功（BuildKit 全部步骤 DONE）
2. `HPC/bwa/README.md` — 新增版本行
3. `HPC/bwa/doc/image-info.yml` — 新增 tag 条目
4. `HPC/bwa/meta.yml` — 新增 `0.7.18-oe2403sp4` 版本路径条目

Docker 镜像的构建和推送阶段均成功完成（`[Build] finished`、`[Push] finished`），失败仅发生在 CI 后置的 `[Check]` 测试验证阶段。测试脚本 `bwa_test.sh` 位于 CI 基础设施的 `eulerpublisher` Python 包路径下，不属于 PR 修改范围。Dockerfile 中构建和安装步骤全部正确执行。

## 修复方向

### 方向 1（置信度: 高）
CI 运维人员修复 `eulerpublisher` 包中的 `bwa_test.sh` 行尾符问题：将文件从 CRLF 转换为 LF，确保 shebang 行 `#!/bin/sh` 不以 `\r` 结尾。操作方式可以是重新发布修复后的 `eulerpublisher` Python 包，或在 CI runner 上直接修复已安装的该文件。PR 作者无需对本次 PR 做任何修改。

## 需要进一步确认的点
（无需进一步确认——根因明确，Docker 构建完整成功，失败完全由 CI 基础设施的测试脚本 CRLF 问题导致。）
