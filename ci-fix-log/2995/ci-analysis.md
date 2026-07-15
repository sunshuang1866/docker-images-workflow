# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: /bin/sh^M, bad interpreter, bwa_test.sh, CRLF, carriage return

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 系统 `eulerpublisher` 包内测试脚本）
- 失败原因: CI 测试基础设施中 `eulerpublisher` 软件包的 `bwa_test.sh` 测试脚本使用了 Windows 风格换行符（CRLF，即 `\r\n`），导致 shebang 行被解析为 `#!/bin/sh\r`（含回车符 `^M`），shell 无法找到 `/bin/sh\r` 这个解释器，报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联
**本次失败与 PR 变更无关。** Docker 镜像构建（Dockerfile 中 `RUN yum install ...`、`make` 编译 bwa）和推送均成功完成，日志中可见 `#7 DONE 199.0s`、`[Build] finished`、`[Push] finished`、镜像 manifest 推送成功。失败发生在 CI 框架层的 `[Check]` 测试阶段——`eulerpublisher` 内置的 `bwa_test.sh` 测试脚本自身存在 CRLF 换行问题，与本次 PR 新增的 bwa Dockerfile 没有任何关联。

## 修复方向

### 方向 1（置信度: 高）
这是 CI 基础设施问题，Code Fixer **无需处理**。CI 运维人员需要将 `eulerpublisher` 包中的 `tests/container/app/bwa_test.sh` 文件的换行符从 CRLF 转换为 LF（Unix 风格换行），例如在对应仓库中执行 `dos2unix` 或 `sed -i 's/\r$//'`。

## 需要进一步确认的点
- 确认 `eulerpublisher` 仓库中 `tests/container/app/bwa_test.sh` 是否确实包含 CRLF 换行符（查看该文件的 git 属性或 hexdump 即可确认）。
- 确认该测试脚本是 eulerpublisher 新版本引入的问题，还是历史遗留问题（此前没有 bwa 镜像触发过该测试路径）。
- 确认修复后需验证无其他应用镜像的测试脚本存在同类 CRLF 问题。
