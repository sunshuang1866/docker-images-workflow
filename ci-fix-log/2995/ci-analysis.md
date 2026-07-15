# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施脚本）
- 失败原因: `eulerpublisher` 包内的 `bwa_test.sh` 测试脚本使用了 Windows 风格的 CRLF 换行符，导致 shebang 行 `#!/bin/sh` 被内核解析为 `#!/bin/sh\r`（`\r` 即 `^M`），系统找不到名为 `"/bin/sh\r"` 的解释器，报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联

与 PR 变更**无关**。PR 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及对应元数据文件。Docker 镜像构建和推送阶段均成功完成（日志中 `[Build] finished`、`[Push] finished`、`#8 DONE 8.4s`）。失败发生在 CI 后处理 [Check] 阶段，由 CI 工具 `eulerpublisher` 自带的 bwa 测试脚本行尾符问题导致，属于基础设施缺陷，与 PR 代码无关。

## 修复方向

### 方向 1（置信度: 高）
CI 运维团队修复 `eulerpublisher` 包中 `tests/container/app/bwa_test.sh` 脚本的行尾符，将 CRLF 转换为 LF。可通过 `dos2unix` 或 `sed -i 's/\r$//'` 完成。此修复需在 CI runner 基础环境镜像或 `eulerpublisher` 包的部署流程中进行，PR 作者无需修改 Dockerfile。

### 方向 2（置信度: 低）
若 `bwa_test.sh` 是在 `eulerpublisher` 安装过程中从 Git 仓库 clone 获取，需检查 `eulerpublisher` 上游仓库中该文件的行尾符配置（`.gitattributes` 或文件本身的编码），确保 clone 后文件为 LF 行尾。

## 需要进一步确认的点

1. 确认 `bwa_test.sh` 脚本的来源——是随 `eulerpublisher` RPM/pip 包安装的静态文件，还是在 CI 运行时动态生成或 clone 的。需要获取 CI runner 上 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh` 的实际内容确认。
2. 确认同一 CI runner 上是否存在其他应用的测试脚本也有相同行尾符问题（属于系统性缺陷还是 bwa 专属脚本个案）。

## 修复验证要求

无需 PR 侧代码修改。CI 运维修复 `bwa_test.sh` 行尾符后，重新触发构建即可验证。
