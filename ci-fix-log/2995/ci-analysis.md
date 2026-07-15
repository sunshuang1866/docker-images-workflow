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
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `eulerpublisher` 包内测试脚本 `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`
- 失败原因: `bwa_test.sh` 脚本包含 Windows 风格换行符（CRLF），导致 shebang `#!/bin/sh` 被解析为 `#!/bin/sh\r`，内核无法找到名为 `/bin/sh\r` 的解释器，报 `bad interpreter: No such file or directory`

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及相关元数据文件。Docker 镜像构建和推送均已成功完成（日志中 `[Build] finished`、`[Push] finished`、`#7 DONE 199.0s`、`#8 DONE 8.4s`），所有编译步骤正常通过。失败发生在 CI 流水线的 `[Check]` 阶段，原因是指向 `eulerpublisher` 自带测试脚本存在 CRLF 行尾问题——该脚本不属于本次 PR 变更范围。

## 修复方向

### 方向 1（置信度: 高）
`eulerpublisher` 包中 `bwa_test.sh` 文件含有 CRLF 行尾，需将其转换为 LF（Unix 风格换行符）。修复应在上游 `eulerpublisher` 仓库中进行（使用 `dos2unix` 或 `sed -i 's/\r$//'`），随后更新 CI 构建节点上的 `eulerpublisher` 包。

## 需要进一步确认的点
1. 确认 `eulerpublisher` 仓库中 `tests/container/app/bwa_test.sh` 的行尾格式（是源文件就有 CRLF，还是克隆/安装过程中引入的）
2. 确认 CI 节点上其他测试脚本是否也存在同样的 CRLF 问题（是否存在系统性影响）
3. 确认 `eulerpublisher` 包的版本号，以便在对应分支/tag 上修复
