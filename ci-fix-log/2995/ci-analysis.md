# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行符
- 新模式症状关键词: `bad interpreter`, `^M`, `No such file or directory`, `bwa_test.sh`

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 工具 eulerpublisher 安装包内的测试脚本）
- 失败原因: CI 测试框架 `eulerpublisher` 自带的 `bwa_test.sh` 脚本包含 Windows 风格换行符（CRLF，`\r\n`），shebang 行 `#!/bin/sh\r` 中的回车符 `\r`（日志中显示为 `^M`）导致内核无法找到名称为 `/bin/sh\r` 的解释器，测试阶段直接失败。

### 与 PR 变更的关联
**此次失败与 PR 变更完全无关。** PR 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及相关的 README、image-info.yml、meta.yml 元数据文件。Docker 镜像构建和推送均已成功完成（日志中可见 `#7 DONE 199.0s`、`[Build] finished`、`[Push] finished`、镜像已推送至 registry）。失败完全发生在 CI 后处理阶段执行 eulerpublisher 内置测试脚本时，该脚本的 CRLF 换行符问题是 eulerpublisher 包的自身缺陷。

## 修复方向

### 方向 1（置信度: 高）
该失败为 `infra-error`，属于 CI 工具链 `eulerpublisher` 安装包中 `bwa_test.sh` 的 CRLF 换行符问题。PR 代码无需任何修改。问题应由 CI 基础设施团队在 eulerpublisher 源码仓库中将 `tests/container/app/bwa_test.sh` 的换行符从 CRLF 转换为 LF 后重新发布包来解决，或由 CI 管理员在运行环境中用 `sed -i 's/\r$//'` 预处理该脚本作为临时规避。

## 需要进一步确认的点
- eulerpublisher 包中 `bwa_test.sh` 是否在其他镜像的 Check 阶段也出现同一错误（若仅 bwa 触发则可能该脚本是最近才加入包的）
- eulerpublisher 源码仓库中 `tests/container/app/bwa_test.sh` 的 git 历史，确认 CRLF 是在何时引入的
