# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF编码
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bwa_test.sh, CRLF

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher CI 工具链内置测试脚本）
- 失败原因: CI 工具链 `eulerpublisher` 中的 `bwa_test.sh` 脚本文件使用了 Windows 风格的 CRLF（`\r\n`）行尾，导致 shebang `#!/bin/sh` 被操作系统解析为 `#!/bin/sh\r`（日志中显示为 `/bin/sh^M`）。Linux 系统找不到这个带回车符的解释器路径，报 "bad interpreter: No such file or directory"。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了以下文件：
- `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（全新 Dockerfile，用于 openEuler 24.03-LTS-SP4）
- `HPC/bwa/README.md`（新增一行版本说明）
- `HPC/bwa/doc/image-info.yml`（新增一行版本条目）
- `HPC/bwa/meta.yml`（新增版本路径映射）

Docker 镜像的构建（`#7 DONE 199.0s`）和推送（`[Push] finished`）均完全成功。失败发生在构建成功之后的 CI [Check] 阶段，是 CI 基础设施工具 `eulerpublisher` 自身脚本的行尾编码问题，与 PR 提交的代码变更无任何关联。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施维护者需修复 `eulerpublisher` 包（或该工具所在的 Git 仓库）中的 `tests/container/app/bwa_test.sh` 文件，将其行尾从 CRLF 转换为 LF（Unix 风格）。可使用 `dos2unix bwa_test.sh` 或 `sed -i 's/\r$//' bwa_test.sh` 执行转换。

### 方向 2（置信度: 中）
如果 `eulerpublisher` 在 CI 流程中通过 git clone 获取（日志中可见 `Cloning into 'eulerpublisher'...`），需检查该仓库的 `.gitattributes` 配置，确保 `*.sh` 文件未配置 `text=auto` 或 `eol=crlf` 规则，或在 CI 脚本的 clone 步骤后执行 dos2unix 批处理转换。

## 需要进一步确认的点
1. `eulerpublisher` 中 `bwa_test.sh` 的获取方式——是通过 pip install 安装还是 git clone 拉取；若为 pip 安装，需确认 PyPI 上该包的当前版本是否包含 CRLF 问题。
2. `bwa_test.sh` 的 CRLF 行尾是否同样影响其他镜像（非 bwa）的 [Check] 测试，还是仅 bwa 独有的测试脚本受影响。

## 修复验证要求
无。此失败属于 CI 基础设施问题（infra-error），错误源在 CI 工具链 `eulerpublisher` 自身，Code Fixer 无需对 PR 代码做任何修改。
