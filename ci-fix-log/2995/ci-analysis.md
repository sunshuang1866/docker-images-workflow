# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: bad interpreter, /bin/sh^M, No such file or directory

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher CI 工具包内的测试脚本）
- 失败原因: `bwa_test.sh` 文件使用了 Windows 风格的换行符（CRLF，即 `\r\n`），导致 shebang 行 `#!/bin/sh` 末尾带有不可见的回车符 `\r`（日志中显示为 `^M`），系统尝试查找名为 `/bin/sh\r` 的解释器失败，报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联
**与 PR 无关。** 证据如下：
1. Docker 镜像构建完全成功（`#7 DONE 199.0s`），编译、安装、清理步骤均正常完成，仅有 gcc 编译警告（非错误）。
2. 镜像推送成功（`#8 DONE 8.4s`），`[Build] finished` 和 `[Push] finished` 均正常。
3. 失败仅发生在 CI 流水线的 `[Check]` 阶段，该阶段调用 eulerpublisher 工具包内置的 `bwa_test.sh` 对构建产物进行验证。该脚本属于 CI 基础设施（eulerpublisher 包），不是 PR 提交的文件。
4. PR diff 仅包含 Dockerfile、README.md、image-info.yml、meta.yml 四个文件的新增/修改，不涉及任何 shell 脚本。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施维护者需要将 eulerpublisher 包中的 `tests/container/app/bwa_test.sh` 文件的换行符从 CRLF 转换为 LF。可使用 `dos2unix` 或 `sed -i 's/\r$//'` 处理该文件后重新打包/部署 eulerpublisher。

## 需要进一步确认的点
- 该 `bwa_test.sh` 是否在 eulerpublisher 仓库最新版本中已修复（可能已在后续版本中转换了换行符，当前 CI 节点安装的是旧版本）。
- 如果 eulerpublisher 最新版本中也存在此问题，需向其仓库提交修复（将测试脚本的换行符统一为 LF）。
