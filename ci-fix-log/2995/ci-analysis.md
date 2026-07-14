# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本换行符错误
- 新模式症状关键词: bad interpreter, /bin/sh^M, CRLF, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施文件）
- 失败原因: `eulerpublisher` 包中自带的 `bwa_test.sh` 测试脚本使用了 **Windows 风格换行符（CRLF，即 `\r\n`）** 而非 Unix 风格换行符（LF）。shebang 行 `#!/bin/sh` 末尾携带了不可见的回车符 `\r`（日志中显示为 `^M`），导致系统尝试查找解释器 `/bin/sh^M`，因该路径不存在而报 `bad interpreter`，测试脚本无法执行。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 修改内容为：
1. 新增 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（bwa 0.7.18 on openEuler 24.03-LTS-SP4）
2. 更新 `HPC/bwa/README.md`、`HPC/bwa/doc/image-info.yml`、`HPC/bwa/meta.yml` 文档/元数据

Docker 镜像构建和推送均已成功（日志中 `[Build] finished`、`[Push] finished`、`#8 DONE 199.0s` 均正常），失败仅发生在 CI 的 `[Check]` 阶段——这是 `eulerpublisher` CI 工具的内置测试脚本问题，与 PR 提交的 Dockerfile 和元数据文件无关。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施维护人员需要修复 `eulerpublisher` 包中的 `bwa_test.sh` 文件，将其换行符从 CRLF 转换为 LF。可通过 `dos2unix` 命令或在编辑器中设置换行符格式为 LF 来解决。该修复需要在 `eulerpublisher` 包仓库中完成，不是本 PR 仓库的责任范围。

## 需要进一步确认的点
- 确认 `eulerpublisher` 包的版本，以及该 `bwa_test.sh` 是否在其他镜像的 check 阶段也同样失效（理论上会影响所有 bwa 镜像的 CI check）。
- 如果该 `bwa_test.sh` 是 CI runner 上静态安装的文件，确认是否只需在 runner 上执行一次 `dos2unix` 即可修复（而非更新 `eulerpublisher` 包本身）。
