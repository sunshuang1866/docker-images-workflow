# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试脚本CRLF行尾
- 新模式症状关键词: `^M`, `bad interpreter`, `No such file or directory`, `bwa_test.sh`

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI [Check] 阶段，`eulerpublisher/container/app/app.py:173`
- 失败原因: CI 测试脚本 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 使用了 Windows 风格换行符（CRLF），导致 shebang 行 `#!/bin/sh\r` 被内核解释为搜索名为 `/bin/sh\r`（尾部含回车符）的解释器，该路径不存在，触发 "bad interpreter: No such file or directory" 错误。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增 bwa 镜像的 openEuler 24.03-LTS-SP4 变体（Dockerfile、meta.yml、README.md、image-info.yml），Docker 镜像构建和推送阶段均已成功完成（`[Build] finished`、`[Push] finished`）。失败发生在 `eulerpublisher` CI 工具链内置的测试脚本 `bwa_test.sh`，该脚本位于 CI 系统目录（`/etc/eulerpublisher/tests/...`），不属于 PR 提交的文件。脚本自身的 CRLF 行尾问题是 CI 基础设施侧（`eulerpublisher` 包）的预存缺陷，因 bwa SP4 变体触发了该测试脚本的执行而暴露。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施维护者需将 `eulerpublisher` 包中的 `tests/container/app/bwa_test.sh` 文件的行尾格式从 CRLF 转换为 LF。可通过 `dos2unix` 或 `sed -i 's/\r$//'` 处理该文件，然后重新打包/部署 `eulerpublisher`。**这不是 PR 作者需要处理的问题，PR 代码无需任何修改。**

## 需要进一步确认的点
- 确认 `bwa_test.sh` 的来源：是 `eulerpublisher` Python 包安装时自带的文件，还是 CI 运行时从某个仓库 clone 的。若确认来自 `eulerpublisher` 包，则仅需对该包做一次修复，所有后续 bwa 镜像的 CI 检查均会受益。
- 确认该测试脚本通过何种机制被查找和执行——是否有测试脚本的集中目录，脚本文件名是否按镜像名匹配，以便排查其他镜像的测试脚本是否也存在同样问题。
