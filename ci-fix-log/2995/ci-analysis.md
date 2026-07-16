# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: `^M, bad interpreter, No such file or directory, bwa_test.sh, eulerpublisher`

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施中的测试脚本，非 PR 代码）
- 失败原因: `eulerpublisher` CI 工具包中的 `bwa_test.sh` 测试脚本使用了 Windows 风格（CRLF）换行符，导致 shebang 行 `#!/bin/sh` 末尾携带回车符 `\r`（`^M`），shell 将解释器路径解析为 `/bin/sh\r`，该路径不存在，脚本无法执行。

### 与 PR 变更的关联

**与 PR 变更无关。** PR 变更内容仅有：
1. 新增 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（bwa 0.7.18 编译和构建逻辑）
2. 更新 `HPC/bwa/README.md`（添加新 tag 文档）
3. 更新 `HPC/bwa/doc/image-info.yml`（添加新版本行，修复文件末尾换行）
4. 更新 `HPC/bwa/meta.yml`（添加新条目和新路径）

这些变更均不涉及 `eulerpublisher` 工具包或任何 shell 脚本。Docker 镜像的构建和推送阶段均成功完成（`#7 DONE 199.0s`，`[Build] finished`，`[Push] finished`），失败仅发生在 CI 后置 Check 阶段，由 CI 基础设施自身的测试脚本文件格式问题导致。

## 修复方向

### 方向 1（置信度: 高）
修复 `eulerpublisher` 包中 `bwa_test.sh` 的行尾格式：将文件从 CRLF 转换为 LF。此问题与 PR 代码无关，应由 CI 基础设施维护者在 `eulerpublisher` 仓库中将该测试脚本的换行符统一为 Unix 风格（LF），然后重新发布/部署该包到 CI 运行节点。

## 需要进一步确认的点
- 确认 `eulerpublisher` 包中 `bwa_test.sh` 文件是否确实存在 CRLF 行尾（可通过 `file` 命令或 `cat -A` 在 CI 节点上验证）
- 确认是否有其他同类型测试脚本也存在 CRLF 问题（批量检查 `eulerpublisher/tests/container/app/` 目录下所有 `.sh` 文件）
- 此 PR 的 Dockerfile 本身无任何问题，可在 CI 基础设施修复后重新触发 CI 验证
