# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本Windows换行
- 新模式症状关键词: bad interpreter, ^M, /bin/sh^M, No such file or directory

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `eulerpublisher` CI 工具内置测试脚本 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh` 的 shebang 行
- 失败原因: 该测试脚本包含 Windows 风格换行符（CRLF），导致 shebang `#!/bin/sh` 末尾携带回车符 `\r`（日志中显示为 `^M`），系统将其解释为查找名为 `/bin/sh\r` 的解释器，因该路径不存在而报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及配套元数据文件（README.md、image-info.yml、meta.yml），Docker 镜像构建阶段已完全成功——日志中可见所有编译步骤正常完成（`#7 DONE 199.0s`）、镜像导出并推送成功（`#8 pushing manifest ... done`，`[Build] finished`，`[Push] finished`）。失败发生在 CI 流水线的 `[Check]` 后置测试阶段，由 `eulerpublisher` Python 包内置的 `bwa_test.sh` 脚本因行尾符问题无法执行导致，属于 CI 基础设施缺陷。

## 修复方向

### 方向 1（置信度: 高）
修复 `eulerpublisher` 包中 `tests/container/app/bwa_test.sh` 文件的换行符，将其从 Windows 风格（CRLF）转换为 Unix 风格（LF）。可通过 `dos2unix` 命令或 `sed -i 's/\r$//'` 处理该文件后重新打包发布 eulerpublisher。

## 需要进一步确认的点
- 确认 `bwa_test.sh` 是何时以 CRLF 格式被提交到 eulerpublisher 仓库的，以及是否其他测试脚本（非 bwa 相关）也存在同样问题。
- 确认此前 bwa 的 22.03-lts-sp3 构建是否也经过了同一 `[Check]` 测试阶段——若该检查是近期新增的，则可解释为何旧版本未触发此问题。

## 修复验证要求
无需 code-fixer 处理。本失败为 CI 基础设施（eulerpublisher 测试脚本行尾符）问题，应由 CI 平台维护方修复 `bwa_test.sh` 文件的换行符后重新发布 eulerpublisher 包。
