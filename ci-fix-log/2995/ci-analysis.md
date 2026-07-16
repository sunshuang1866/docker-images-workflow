# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: `bad interpreter`, `^M`, `No such file or directory`, `bwa_test.sh`

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher 包安装路径，非 PR 仓库文件）
- 失败原因: CI 基础设施中 eulerpublisher 包的 `bwa_test.sh` 测试脚本使用了 Windows 风格换行符（CRLF）。Shebang 行 `/bin/sh` 末尾附带不可见回车符 `\r`（日志中显示为 `^M`），导致内核将解释器路径解析为 `/bin/sh\r`，该文件不存在，进而报 "bad interpreter: No such file or directory"。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了 BWA 的 openEuler 24.03-LTS-SP4 Dockerfile 及相关元数据文件（README.md、image-info.yml、meta.yml）。Docker 镜像的构建和推送阶段均成功完成（日志中 `#7 DONE 199.0s`、`[Build] finished`、`[Push] finished`），失败仅发生在 CI 流程的 [Check] 阶段——即 eulerpublisher 测试框架对被构建镜像的运行验证步骤，该步骤调用的测试脚本 `bwa_test.sh` 存在 CRLF 行尾格式问题，属于 CI 基础设施缺陷。

## 修复方向

### 方向 1（置信度: 高）
由 CI 基础设施维护者修复 eulerpublisher 包中 `bwa_test.sh` 的行尾格式。该文件位于 eulerpublisher 包的 `tests/container/app/bwa_test.sh`，需要将其从 CRLF（Windows）转换为 LF（Unix）格式。Code Fixer Agent 无需修改任何 PR 文件，此问题应由 CI 运维团队在 eulerpublisher 发布包层面解决。

## 需要进一步确认的点
1. 确认 eulerpublisher 测试脚本仓库中 `bwa_test.sh` 的实际行尾格式（可在 eulerpublisher 源码仓库中运行 `file bwa_test.sh` 或 `git show --raw` 检查）
2. 确认 eulerpublisher 的新版本是否已修复此问题——考虑升级 CI 节点上的 eulerpublisher 包（`pip install -U eulerpublisher`）或重新以 LF 行尾部署测试脚本
3. 如果是近期 eulerpublisher 变更引入的回归，需回溯该文件的 git 历史定位引入点
