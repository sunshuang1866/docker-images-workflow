# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: `/bin/sh^M`, bad interpreter, No such file or directory, CRLF

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 框架 eulerpublisher 的内置测试脚本）
- 失败原因: eulerpublisher 软件包中的 `bwa_test.sh` 测试脚本含有 Windows 风格的 CRLF（`\r\n`）换行符，导致 shebang 行 `#!/bin/sh` 被内核解析为 `#!/bin/sh\r`，无法找到合法的解释器

### 与 PR 变更的关联
**与 PR 变更无关。** PR 的 Dockerfile 构建完全成功（`#7 DONE 199.0s`），编译、安装、导出、推送均正常。失败发生在 CI 框架的 `[Check]` 阶段——eulerpublisher 尝试运行内置的 `bwa_test.sh` 对构建出的镜像做功能验证，但该测试脚本因 CRLF 行尾导致无法执行。这是一个 CI 基础设施问题，非本次 PR 代码引入。

## 修复方向

### 方向 1（置信度: 高）
在 eulerpublisher 源码仓库中，将 `tests/container/app/bwa_test.sh` 的行尾从 CRLF（`\r\n`）转换为 LF（`\n`）。可使用 `dos2unix` 或在 Git 中设置 `core.autocrlf` 防止此类问题再次发生。修复后需在 CI 节点上更新 eulerpublisher 包或重新部署。

## 需要进一步确认的点
- eulerpublisher 中 `bwa_test.sh` 是何时引入的、是否仅该文件存在 CRLF 问题，还是整个测试脚本目录受波及
- 同一 CI runner 上其他应用镜像的 Check 阶段是否近期也出现类似 `/bin/sh^M: bad interpreter` 错误（可确认是否仅为 bwa 测试脚本的问题）
- `bwa_test.sh` 本身的功能内容是否正确（换行符修复后可能暴露出脚本逻辑本身的问题）
