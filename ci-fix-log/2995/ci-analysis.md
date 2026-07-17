# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: `bad interpreter`, `^M`, `No such file or directory`, `bwa_test.sh`, `[Check] test failed`

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher 包安装的测试脚本）
- 失败原因: `bwa_test.sh` 脚本文件的 shebang 行带有 Windows 风格 CRLF 换行符（`\r\n`），导致内核将解释器路径解析为 `/bin/sh\r`（含回车符），该路径不存在，触发 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联
**与 PR 代码变更无关**。PR 变更仅涉及以下文件：
1. `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（新增）
2. `HPC/bwa/README.md`（追加 tag 描述）
3. `HPC/bwa/doc/image-info.yml`（追加 tag 条目）
4. `HPC/bwa/meta.yml`（追加版本映射）

Docker 镜像构建和推送阶段均成功完成（`[Build] finished`、`[Push] finished`）。失败发生在 eulerpublisher 的 `[Check]` 阶段，该阶段调用了 eulerpublisher 包自带的 `bwa_test.sh`，该脚本不属于本仓库，其 CRLF 行尾问题是 CI 基础设施侧的问题，与本 PR 的 Dockerfile 及元数据变更无关。

## 修复方向

### 方向 1（置信度: 高）
将 eulerpublisher 包中的 `bwa_test.sh` 文件的换行符从 CRLF 转换为 LF（Unix 风格）。可使用 `dos2unix` 或 `sed -i 's/\r$//'` 处理该文件。

### 方向 2（置信度: 低）
若 eulerpublisher 是从 git 仓库克隆后安装的，需检查该仓库中 `tests/container/app/bwa_test.sh` 是否因某次提交引入了 CRLF 行尾（可能来自 Windows 环境的 `git clone` 或编辑），需在该仓库中修复并重新部署 eulerpublisher 包。

## 需要进一步确认的点
1. `bwa_test.sh` 的来源：确认该文件来自 eulerpublisher 的 pip 安装包还是从某个 git 仓库克隆安装。若来自 git 仓库，需定位引入 CRLF 的具体提交。
2. 其他应用镜像的测试脚本是否也存在同样的 CRLF 问题（如 `bigdata_test.sh`、`ai_test.sh` 等），可能影响面更广。
3. 该 `bwa_test.sh` 脚本内容是否需要针对 openEuler 24.03-LTS-SP4 做任何适配性更新（当前仅确认行尾格式问题导致脚本完全无法执行）。

## 修复验证要求
修复后需在 CI 环境中重新触发构建，确认 `[Check]` 阶段的 `bwa_test.sh` 能正常执行，不再出现 `bad interpreter` 错误。
