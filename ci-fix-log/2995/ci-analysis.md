# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试脚本CRLF行尾
- 新模式症状关键词: `^M`, `bad interpreter`, `No such file or directory`, `_test.sh`, `bwa_test.sh`

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施中的测试脚本）
- 失败原因: CI 测试框架 `eulerpublisher` 中的 `bwa_test.sh` 文件包含 Windows 风格换行符（CRLF, `\r\n`），导致 shebang 行 `#!/bin/sh` 被内核解析为 `#!/bin/sh\r`，`/bin/sh\r` 作为解释器不存在，脚本执行失败。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像构建（`[Build]` 阶段）和推送（`[Push]` 阶段）均已成功完成，日志中可见完整的 RUN 指令输出（yum 安装、源码编译 bwa 0.7.18、二进制输出、构建工具卸载及清理），最终镜像导出和推送均为 DONE 状态。失败仅发生在 CI `[Check]` 阶段运行测试脚本时，该测试脚本属于 CI 基础设施组件 `eulerpublisher` 软件包，不在 PR 的变更范围内。

PR 变更仅包含：
- 新增 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`
- 更新 `HPC/bwa/README.md`、`HPC/bwa/doc/image-info.yml`、`HPC/bwa/meta.yml`

这些变更均不涉及 shell 脚本，也不涉及 `eulerpublisher` 测试设施。

## 修复方向

### 方向 1（置信度: 高）
由 CI 基础设施维护者修复 `eulerpublisher` 软件包中的 `bwa_test.sh` 文件，将其换行符从 CRLF（`\r\n`）转换为 LF（`\n`）。通常通过在 Linux 环境执行 `dos2unix` 或 `sed -i 's/\r$//'` 即可修复。修复后需重新安装/部署 `eulerpublisher` 包到 CI runner 节点。

## 需要进一步确认的点
- `bwa_test.sh` 是否存在其他因 CRLF 导致的内容问题（如变量展开异常），修复后需完整执行一次 check 流程验证
- 确认该 CRLF 问题是仅影响 `bwa_test.sh`，还是 `eulerpublisher` 打包过程中存在系统性的换行符错误（其他 `_test.sh` 文件也可能受影响）
- 如果 CI runner 节点无法由开发者直接修改，需联系 CI 平台管理员或提 issue 到 `eulerpublisher` 仓库报告此问题
