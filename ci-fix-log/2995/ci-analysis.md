# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行符
- 新模式症状关键词: /bin/sh^M, bad interpreter, No such file or directory, CRLF, Windows line endings

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施 eulerpublisher 包中的测试脚本）
- 失败原因: eulerpublisher CI 工具包内置的 `bwa_test.sh` 测试脚本使用了 Windows 风格换行符（CRLF）。Shebang 行 `#!/bin/sh` 末尾附带了回车符 `\r`（日志中显示为 `^M`），导致内核尝试查找名为 `/bin/sh\r` 的解释器，该文件不存在，触发 "bad interpreter: No such file or directory" 错误。

### Docker 构建状态
日志清晰表明 Docker 镜像构建和推送**均已完成并成功**：
- `#7 DONE 199.0s` — 构建完成
- `[Build] finished` — 构建阶段结束
- `[Push] finished` — 推送阶段结束
- 仅 `[Check]` 阶段因测试脚本自身换行符问题失败

### 与 PR 变更的关联
PR 变更内容为新增 bwa 0.7.18 Dockerfile 及相关元数据文件（README.md、image-info.yml、meta.yml），变更本身与 CI 失败**无直接因果关系**。失败根源在 CI 基础设施的 eulerpublisher 包中 `bwa_test.sh` 文件的换行符格式问题，非此 PR 的代码变更所引入。

## 修复方向

### 方向 1（置信度: 高）
修复 eulerpublisher 仓库中 `tests/container/app/bwa_test.sh` 的换行符：将 CRLF（`\r\n`）转换为 LF（`\n`）。该问题通常由以下原因引起：
- 该测试脚本在 Windows 环境创建/编辑后提交到 eulerpublisher 仓库
- git 配置 `core.autocrlf` 导致 checkout 时 LF 被转换为 CRLF

修复后需重新发布 eulerpublisher 包或更新 CI runner 上的测试脚本文件。

## 需要进一步确认的点
- eulerpublisher 仓库中 `bwa_test.sh` 的原始换行符格式（是源文件本身为 CRLF，还是 CI 环境 git checkout 时转换导致）
- 是否存在其他同样受 CRLF 影响的测试脚本（如果 eulerpublisher 有批量添加新测试脚本的操作）
- CI runner 的 git 全局配置（`core.autocrlf`）是否设置为 `true` 或 `input`
