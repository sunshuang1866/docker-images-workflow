# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本行尾格式错误
- 新模式症状关键词: `bad interpreter`, `^M`, `No such file or directory`, `bwa_test.sh`, CRLF

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施中的测试脚本，非 PR 代码）
- 失败原因: `eulerpublisher` 包中分发的 `bwa_test.sh` 测试脚本包含 Windows 风格换行符（CRLF），shebang 行 `#!/bin/sh` 末尾携带 `\r`（`^M`），导致系统尝试查找名为 `/bin/sh\r` 的解释器，因不存在而失败。Docker 镜像的构建（[Build]）和推送（[Push]）阶段均已完成且成功，仅 CI 的 [Check] 测试阶段因脚本格式问题失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 bwa 0.7.18 在 openEuler 24.03-lts-sp4 上的 Dockerfile（及配套的 README.md、image-info.yml、meta.yml 更新）。日志显示 Docker 构建完全成功：依赖安装、BWA 源码编译（gcc 编译所有 .o 文件无一报错）、二进制安装、构建工具清理、镜像推送均正常完成。失败发生在 eulerpublisher 测试框架调用 `bwa_test.sh` 时，该脚本是 CI 基础设施组件（位于 `/etc/eulerpublisher/`），不来自 PR 提交的任何文件。

## 修复方向

### 方向 1（置信度: 高）
报告给 CI 基础设施维护者，要求修复 `eulerpublisher` 包中的 `bwa_test.sh` 文件行尾格式（将 CRLF 转换为 LF）。可使用 `dos2unix` 或 `sed -i 's/\r$//'` 处理该文件后重新打包/分发 eulerpublisher。

## 需要进一步确认的点
- 确认 `eulerpublisher` 包中 `bwa_test.sh` 的来源（是从上游仓库打包时引入的 CRLF，还是在 CI 环境中某个步骤错误转换了行尾）。
- 确认其他镜像（非 bwa）的 CI [Check] 测试在当前同一批 CI 运行中是否也有类似失败（若全量失败，说明 eulerpublisher 包整体有问题；若仅 bwa 失败，说明问题局限在 `bwa_test.sh` 这一文件）。

## 修复验证要求
无需 PR 代码修改。此失败为 infra-error，Code Fixer 无需处理。
