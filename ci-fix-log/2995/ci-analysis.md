# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, ^M, test failed, bwa_test.sh, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-10 11:58:05,860 - INFO - [Build] finished
2026-07-10 11:58:05,860 - INFO - [Push] finished
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI runner 系统安装的 eulerpublisher 测试脚本）
- 失败原因: eulerpublisher 包中自带的 `bwa_test.sh` 测试脚本包含 Windows 风格 CRLF 换行符（`\r\n`），导致 shebang 行 `#!/bin/sh` 末尾附带回车符 `\r`（显示为 `^M`），Linux 内核将其解析为解释器路径 `/bin/sh\r`，因该路径不存在而报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了 bwa 在 openEuler 24.03-lts-sp4 上的 Dockerfile、更新了 README.md、image-info.yml 和 meta.yml。Docker 镜像构建和推送均完全成功（`[Build] finished` + `[Push] finished`，BuildKit 层缓存 `#7 DONE 199.0s`，`#8 DONE 8.4s`）。失败发生在 CI 后处理阶段的 `[Check]` 步骤，由 CI runner 上系统级安装的 eulerpublisher 软件包缺陷导致，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施维护者需检查 eulerpublisher 软件包中 `bwa_test.sh`（路径为 `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`）的文件编码，使用 `dos2unix` 或等效工具将 CRLF 换行符转换为 LF，重新打包发布。

## 需要进一步确认的点
- 确认 CI runner 上 eulerpublisher 软件包的版本和来源（是否为某个已知有缺陷的构建版本）。
- 检查 eulerpublisher 测试脚本目录下是否还有其他脚本同样存在 CRLF 问题（`file /usr/etc/eulerpublisher/tests/container/app/*.sh | grep CRLF`）。
