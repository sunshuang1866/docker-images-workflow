# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本换行符不兼容
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher 包中的测试脚本）
- 失败原因: CI 工具 `eulerpublisher` 内置的 `bwa_test.sh` 测试脚本使用了 Windows 换行符（CRLF，即 `\r\n`），导致 shebang 行 `#!/bin/sh` 末尾附带不可见的回车符 `\r`（日志中显示为 `^M`），操作系统无法找到名为 `/bin/sh\r` 的解释器，报告 "bad interpreter: No such file or directory"。

### 与 PR 变更的关联
**与 PR 无关。** Docker 镜像的构建和推送阶段均已成功完成（日志中可见 `[Build] finished` 和 `[Push] finished`，构建产物 sha256 已生成并推送至 registry），失败仅发生在 eulerpublisher 的 [Check] 后置校验阶段。PR 变更仅涉及新增 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`、更新 README.md、image-info.yml 和 meta.yml，不包含也不影响 `bwa_test.sh` 测试脚本。

## 修复方向

### 方向 1（置信度: 高）
`eulerpublisher` 包中的 `bwa_test.sh` 文件含有 Windows 换行符（CRLF）。需要将 `eulerpublisher` 源码仓库中 `tests/container/app/bwa_test.sh` 的行尾序列从 CRLF 转换为 LF（Unix 换行符），并重新发布/安装 eulerpublisher 包到 CI runner 上。Code Fixer 无需修改本 PR 的任何文件。

## 需要进一步确认的点
- 确认 `eulerpublisher` 源码仓库中 `tests/container/app/bwa_test.sh` 是否确实为 CRLF 行尾，以及该文件是何时引入、是否其他应用的测试脚本也存在同类问题。
- 确认 eulerpublisher 包在 CI runner 上的版本及更新机制。
