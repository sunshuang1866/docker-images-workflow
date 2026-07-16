# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行符
- 新模式症状关键词: bad interpreter, /bin/sh^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 工具 eulerpublisher 安装的测试脚本）
- 失败原因: `bwa_test.sh` 测试脚本文件的 shebang 行以 Windows 换行符（CRLF, `\r\n`）结尾，而非 Unix 换行符（LF, `\n`）。shell 在执行时将 `^M`（即 `\r`）视为 shebang 解释器路径的一部分，尝试以 `/bin/sh\r` 作为解释器执行脚本，因不存在名为 `/bin/sh\r` 的可执行文件而报 "bad interpreter: No such file or directory"。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及修改元数据文件（README.md、image-info.yml、meta.yml），Docker 构建与推送阶段全部成功完成（日志中可见 `#8 exporting to image` → `#8 pushing manifest ... done` 以及 `[Build] finished`、`[Push] finished`）。失败发生在 CI 工具的 [Check] 阶段：`eulerpublisher` 包自带的 `bwa_test.sh` 测试脚本本身因 Windows 换行符问题无法执行。

## 修复方向

### 方向 1（置信度: 高）
该失败属于 CI 基础设施问题，与本次 PR 的代码变更无关。Dockerfile 构建流程和镜像本身没有问题。修复应由 **CI 工具维护者**完成：将 `eulerpublisher` 仓库中的 `bwa_test.sh` 文件的换行符从 CRLF 转换为 LF（Unix 格式），重新打包/发布 `eulerpublisher` 包后，CI 流水线即可恢复正常。

## 需要进一步确认的点
- 确认 `eulerpublisher` 仓库中 `tests/container/app/bwa_test.sh` 文件的换行格式（是否为 CRLF），可通过 `file` 命令或 `cat -v` 查看文件内容中的 `^M` 字符来验证。
- 确认其他应用的测试脚本（如 `*_test.sh`）是否也存在同样的 CRLF 换行符问题（批量检查可避免后续同类失败）。
