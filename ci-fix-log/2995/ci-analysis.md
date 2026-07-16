# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CRLF行尾致脚本解释器异常
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bwa_test.sh, CRLF

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `eulerpublisher` 包安装路径下的 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（shebang 行）
- 失败原因: `eulerpublisher` 测试包中的 `bwa_test.sh` 脚本包含 Windows 风格 CRLF 行尾（`\r\n`），导致 shebang 行被解析为 `/bin/sh^M`，内核无法找到名为 `/bin/sh\r` 的解释器，报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了 BWA 0.7.18 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Docker 镜像构建和推送阶段均成功完成（日志中 `[Build] finished`、`[Push] finished` 及 `#7 DONE 199.0s` 均确认）。失败发生在 CI 流水线的 `[Check]` 阶段，由 `eulerpublisher` 包内预置的测试脚本因 CRLF 行尾问题无法执行导致，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
CI 维护者需要修复 `eulerpublisher` 包中的 `tests/container/app/bwa_test.sh` 文件，将其行尾从 CRLF（`\r\n`）转换为 LF（`\n`）。可通过 `dos2unix` 或 `sed -i 's/\r$//'` 处理该文件后重新发布 `eulerpublisher` 包。

## 需要进一步确认的点
- 确认 `eulerpublisher` 包中是否仅有 `bwa_test.sh` 一个测试脚本存在 CRLF 问题，还是整个 `tests/` 目录下的多个脚本均受影响（全局排查）。
- 确认该 CRLF 问题是 `eulerpublisher` 包发布流程中的偶发缺陷还是持续性问题，如果是持续性问题则需要修复包的构建/发布流水线。
