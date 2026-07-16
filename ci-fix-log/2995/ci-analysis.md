# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: /bin/sh^M, bad interpreter, No such file or directory, bwa_test.sh, CRLF

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: eulerpublisher 测试框架的 `bwa_test.sh` 脚本（CI 基础设施，非 PR 变更文件）
- 失败原因: `eulerpublisher` 测试框架中的 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh` 脚本文件存在 Windows 风格的 CRLF 行尾符（`\r\n`）。shebang 行 `#!/bin/sh` 被解析为 `#!/bin/sh\r`，Linux 内核在查找名为 `/bin/sh\r`（带回车字符）的解释器时失败，输出 `/bin/sh^M: bad interpreter: No such file or directory`。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 变更内容为：
1. 新增 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` — 编译和构建流程在日志中已成功完成（`#7 DONE 199.0s`，`[Build] finished`，`[Push] finished`，镜像成功推送到 registry）
2. 更新 `HPC/bwa/README.md` — 文档
3. 更新 `HPC/bwa/doc/image-info.yml` — 元数据
4. 更新 `HPC/bwa/meta.yml` — 镜像注册

以上所有 PR 文件均不含 CRLF 行尾符，且 Docker 镜像构建本身完全成功。失败发生在 CI 基础设施的测试脚本执行阶段（`[Check]` 步骤），是 `eulerpublisher` 框架的部署问题。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施维护者需要将 `eulerpublisher` 测试框架中的 `bwa_test.sh` 脚本从 CRLF 行尾符转换为 LF 行尾符。可使用 `dos2unix` 或在 git 中配置 `core.autocrlf=input` 防止此类问题。这不是 PR 作者需要处理的。Code Fixer 无需对此 PR 做任何修改。

## 需要进一步确认的点
- 确认 `eulerpublisher` 仓库中 `tests/container/app/bwa_test.sh` 文件的 git 属性设置（是否配置了 `*.sh text eol=lf` 在 `.gitattributes` 中）
- 确认该测试框架是通过 `pip install` 还是源码 clone 方式部署到 CI runner 上的，两者的行尾转换行为不同
