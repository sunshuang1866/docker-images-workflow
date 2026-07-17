# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: ^M, bad interpreter, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施 eulerpublisher 包内置的测试脚本）
- 失败原因: eulerpublisher 包中 `bwa_test.sh` 文件使用了 **Windows 风格换行符（CRLF，`\r\n`）**，导致 shebang 行被解释为 `/bin/sh\r`（带回车符），操作系统找不到名含 `\r` 的解释器，报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联
**此次失败与 PR 变更完全无关。** PR 仅新增了以下 4 个文件/变更：
- `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（新 Dockerfile）
- `HPC/bwa/README.md`（新增 1 行版本列表条目）
- `HPC/bwa/doc/image-info.yml`（新增 1 行版本条目）
- `HPC/bwa/meta.yml`（新增 1 个版本映射条目）

以上所有文件均为纯文本/配置文件，不包含任何 shell 脚本。Docker 镜像构建本身已成功完成（Build + Push 均通过 `#8 DONE`），失败发生在 CI 框架（eulerpublisher）的 [Check] 后测试阶段，因 eulerpublisher 内置的 `bwa_test.sh` 文件存在 CRLF 行尾问题而导致测试无法启动。

## 修复方向

### 方向 1（置信度: 高）
**CI 基础设施维护**：eulerpublisher 包的 `tests/container/app/bwa_test.sh` 文件需要修复 CRLF → LF 换行符转换。这是 CI 基础设施层面（eulerpublisher 软件包）的问题，应由 CI 平台维护人员处理，**Code Fixer 无需对仓库做任何修改**。

## 需要进一步确认的点
- 确认 `bwa_test.sh` 文件的 CRLF 行尾是否为 eulerpublisher 发版时引入的普遍问题（即同一版本的 eulerpublisher 包中是否还有其他测试脚本也存在 CRLF 行尾问题）。
- 确认 eulerpublisher 的安装方式（pip install 或源码构建），以确定修复后是否需要重新发布 eulerpublisher 包。

## 修复验证要求
无。此次失败为 CI 基础设施问题，不需要对仓库文件做任何修复，也不涉及正则 patch 外部源文件。
