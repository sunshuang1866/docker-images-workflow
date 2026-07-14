# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, No such file or directory, ^M, /bin/sh^M

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 工具链安装路径，非 PR 修改范围）
- 失败原因: CI 流水线 [Check] 阶段调用容器测试脚本 `bwa_test.sh` 时，该脚本的 shebang 行（`#!/bin/sh`）末尾带有 Windows 换行符（`\r`），导致系统尝试查找解释器 `/bin/sh\r`（即 `/bin/sh^M`），该文件不存在，脚本无法执行。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像构建（[Build] 和 [Push] 阶段）已成功完成：
- 所有 17 个构建步骤（yum install、源码下载、编译、安装、清理）均通过，无错误。
- 镜像导出和推送成功（`#8 DONE 8.4s`，`[Build] finished`，`[Push] finished`）。
- 失败仅发生在 [Check] 阶段，该阶段调用的是 CI 工具链 `eulerpublisher` 安装目录下的 `bwa_test.sh` 测试脚本，该脚本的 CRLF 行尾问题属于 CI 基础设施缺陷，与本次 PR 新增的 Dockerfile、README.md、image-info.yml、meta.yml 均无任何关联。

## 修复方向

### 方向 1（置信度: 高）
CI 运维侧修复：对 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 执行 `dos2unix` 或 `sed -i 's/\r$//'` 转换，将文件的 CRLF 行尾改为 LF 行尾，使 shebang 中的 `#!/bin/sh` 可被正常识别。

## 需要进一步确认的点
- 确认 `bwa_test.sh` 在 CI 工具链源码仓库中的格式是否为 LF，若源文件本身是 LF，则问题出在 CI 节点上的文件分发/安装环节。
- 确认同批次其他镜像（非 bwa）的 [Check] 测试是否也受此影响——若 `eulerpublisher` 的全部测试脚本均存在 CRLF 问题，影响面可能更广。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用。本次错误属于 CI 基础设施缺陷，无需修改 PR 代码。
