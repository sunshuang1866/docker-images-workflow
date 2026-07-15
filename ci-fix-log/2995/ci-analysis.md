# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: /bin/sh^M, bad interpreter, CRLF, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI 编排工具 `eulerpublisher` 安装目录下的测试脚本 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`
- 失败原因: `bwa_test.sh` 脚本文件的换行符为 Windows 风格（CRLF `\r\n`）而非 Unix 风格（LF `\n`），导致 shebang 行 `#!/bin/sh` 实际被解析为 `#!/bin/sh\r`。内核尝试查找名为 `/bin/sh\r` 的解释器，因该路径不存在而报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及配套元数据文件（README.md、image-info.yml、meta.yml），Docker 镜像构建和推送均已成功完成（日志中 `[Build] finished`、`[Push] finished`）。失败发生在 CI 工具链的 `[Check]` 阶段，由 `eulerpublisher` 包内置的 `bwa_test.sh` 测试脚本自身格式问题导致，属于 CI 基础设施缺陷。

## 修复方向

### 方向 1（置信度: 高）
`eulerpublisher` 仓库中的 `tests/container/app/bwa_test.sh` 文件需要将换行符从 CRLF 转换为 LF。在 `eulerpublisher` 仓库根目录执行 `dos2unix tests/container/app/bwa_test.sh` 或通过 `sed -i 's/\r$//' tests/container/app/bwa_test.sh` 转换后重新发布 `eulerpublisher` 包。

### 方向 2（置信度: 低）
如果 `eulerpublisher` 仓库中根本不存在 `bwa_test.sh` 文件，则说明 CI 在运行时从其他源动态生成了该脚本，且生成过程未正确处理换行符。需要排查 `eulerpublisher` 中生成/复制测试脚本的逻辑。

## 需要进一步确认的点

1. 确认 `eulerpublisher` 仓库中是否确实存在 `tests/container/app/bwa_test.sh` 文件，以及其当前换行符格式。
2. 确认该脚本是何时被添加到 `eulerpublisher` 仓库的——如果是在本 PR 之前不久才添加的，则可能是添加时引入的格式问题。
3. 排除一种边缘情况：确认 CI 的 `[Check]` 步骤是否有从 PR 分支动态拉取测试脚本的机制。若测试脚本实际来源于 PR 分支目录（而非 `eulerpublisher` 包），则需要修复的是 PR 分支中的对应文件路径。
