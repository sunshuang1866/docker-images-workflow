# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, ^M, /bin/sh^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking .../bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施测试脚本，非 PR 变更文件）
- 失败原因: CI 检查阶段的测试脚本 `bwa_test.sh` 文件中包含 Windows 风格换行符（CRLF），导致 shebang `#!/bin/sh` 被解析为 `#!/bin/sh\r`，Linux 系统找不到名为 `/bin/sh\r` 的解释器，脚本无法执行。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及更新了 `README.md`、`image-info.yml`、`meta.yml`。Docker 镜像构建阶段已完全成功（`#7 DONE 199.0s`，编译无错误，镜像已构建并推送至 registry），失败发生在构建完成后的「Check」阶段——由 CI 基础设施自带的 `bwa_test.sh` 脚本执行失败引发，该脚本不属于本仓库代码，不受 PR 变更影响。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施维护者需要修复 `eulerpublisher` 工具包中的 `bwa_test.sh` 测试脚本：将文件的换行符从 CRLF（`\r\n`）转换为 LF（`\n`）。可使用 `dos2unix` 或 `sed -i 's/\r$//'` 对 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh` 进行处理后重新部署。PR 作者无需修改本仓库代码。

## 需要进一步确认的点
- 确认 `eulerpublisher` 工具包的版本和发布流程，排查该 `bwa_test.sh` 脚本是否在其他镜像的 Check 阶段也会触发同类问题。
- 确认该测试脚本是 CI 镜像/RPM 自带的文件，还是由 CI 流水线中某步骤动态生成的；如果是动态生成的，需排查生成逻辑中引入 CRLF 的环节。

## 修复验证要求
不适用——此失败为 CI 基础设施问题，PR 代码无需修改。修复应由 CI 平台维护者在 eulerpublisher 工具包层面进行，无需 code-fixer 介入。
