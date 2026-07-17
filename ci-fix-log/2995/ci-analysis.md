# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI [Check] 阶段，`eulerpublisher` 包中的测试脚本 `bwa_test.sh`
- 失败原因: CI 工具 `eulerpublisher` 的内置测试脚本 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh` 使用了 Windows 换行符（CRLF, 即 `\r\n`）而非 Unix 换行符（LF, 即 `\n`）。shell 读取 shebang `#!/bin/sh\r` 时，将 `\r`（`^M`）视为解释器路径的一部分，导致系统尝试查找不存在的解释器 `/bin/sh\r`，因此报 "bad interpreter: No such file or directory"。

### 与 PR 变更的关联
**与 PR 无关。** PR 新增的 Dockerfile 构建和镜像推送均完全成功：
- `#7 [2/2] RUN yum -y install make gcc zlib-devel ...` → `#7 DONE 199.0s`（编译成功）
- `#8 exporting to image` → `#8 DONE 8.4s`（镜像导出成功）
- `[Build] finished` → `[Push] finished`（构建和推送均已完成）
- 失败仅发生在 CI 自身的 [Check] 后置测试阶段，测试脚本 `bwa_test.sh` 位于 `eulerpublisher` 安装目录下，**不是 PR 引入的文件**。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施侧修复：将 `eulerpublisher` 包中的 `bwa_test.sh` 脚本从 CRLF 转换为 LF 换行符。这不是 PR 作者或 Code Fixer 可以修复的问题，需要 CI 运维人员修正 `eulerpublisher` 包中的测试脚本文件格式。Code Fixer 无需处理此 PR。

## 需要进一步确认的点
- 确认 `bwa_test.sh` 文件是哪个版本的 `eulerpublisher` 包引入的，该版本是否在 Windows 环境下生成或编辑过。
- 确认是否有其他镜像的测试脚本也存在同样的 CRLF 问题（可通过 `file *.sh | grep CRLF` 检查）。
