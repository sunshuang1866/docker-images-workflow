# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bin/sh, CRLF, line endings

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: eulerpublisher 包的测试脚本 `bwa_test.sh`（路径 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`）
- 失败原因: CI 工具链 `eulerpublisher` 中包含的 bwa 测试脚本使用了 Windows 风格的 CRLF 换行符（`\r\n`），导致 shebang 行被内核解析为 `/bin/sh\r`，该路径不存在，shell 拒绝执行。

### 与 PR 变更的关联

**与 PR 无关。** 本次 PR 变更仅涉及：
- 新增 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（Docker 构建文件）
- 更新 `HPC/bwa/README.md`（文档）
- 更新 `HPC/bwa/doc/image-info.yml`（元数据）
- 更新 `HPC/bwa/meta.yml`（版本元数据）

Docker 镜像的构建和推送均已成功完成（日志中可见 `[Build] finished`、`[Push] finished`、以及 buildx 推送到 registry 的完整记录）。失败发生在 CI 后处理阶段的 `[Check]` 步骤，由 eulerpublisher 工具中预置的 `bwa_test.sh` 测试脚本因 CRLF 行尾问题无法执行导致，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
`eulerpublisher` 工具包中的 `bwa_test.sh` 测试脚本包含 Windows 风格换行符（CRLF），需在 eulerpublisher 工具侧修复：将 `tests/container/app/bwa_test.sh` 的行尾从 CRLF 转换为 LF（`dos2unix` 或在发布打包流程中统一处理）。此为 CI 基础设施层面的问题，**Code Fixer 无需对 PR 代码做任何修改**。

## 需要进一步确认的点
- 确认 `bwa_test.sh` 的来源：是随 eulerpublisher 包一起安装的，还是在 CI 流水线中从某个仓库动态拉取的。若为后者，需找到对应仓库并修复行尾。
- 确认是否有其他应用的测试脚本也存在同样的 CRLF 问题（可能影响面不止 bwa）。
