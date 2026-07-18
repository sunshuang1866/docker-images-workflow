# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: `bad interpreter`, `No such file or directory`, `^M`, `bwa_test.sh`, `eulerpublisher`

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI Runner 上的 `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`
- 失败原因: `eulerpublisher` 包中的 `bwa_test.sh` 测试脚本含有 Windows 风格换行符（CRLF），导致 shebang `#!/bin/sh\r` 被解析为查找 `/bin/sh^M`（不存在的解释器），系统报 "bad interpreter: No such file or directory"。Docker 镜像构建和推送均成功完成（`[Build] finished`、`[Push] finished`），失败仅发生在 CI 后置的镜像 Check 阶段。

### 与 PR 变更的关联
PR 变更与此次失败**无直接关联**。该 PR 新增了 bwa 0.7.18 的 openEuler 24.03-LTS-SP4 Dockerfile 及相关元数据文件，Docker 构建在 x86_64 上全部成功（编译输出正常、镜像导出和推送均完成）。失败点是 `eulerpublisher` CI 工具包自带的 `bwa_test.sh` 测试脚本存在 CRLF 行尾问题，该脚本由 CI 基础设施维护，不由 PR 代码控制。

## 修复方向

### 方向 1（置信度: 中）
`eulerpublisher` 包中的 `tests/container/app/bwa_test.sh` 文件需要将行尾从 CRLF 转换为 LF。这需要 `eulerpublisher` 包的维护者执行 `dos2unix` 或等效操作后重新发布该包。该修复不在当前 PR 仓库的可控范围内。

### 方向 2（置信度: 低）
如果 `bwa_test.sh` 是由 CI 流程从某 Git 仓库动态拉取/克隆而来（参照日志中 `git clone` `eulerpublisher` 的操作），则可能是该上游 Git 仓库中该文件本身存在 CRLF 问题，需要在对应的上游仓库中修复。

## 需要进一步确认的点
1. `bwa_test.sh` 的来源：确认该脚本是 `eulerpublisher` pip 包的静态文件，还是 CI 流程中从其他仓库动态克隆的文件。
2. 该测试脚本是否在 bwa 的其他 OS 版本（如 22.03-lts-sp3）的 CI 构建中也同样被调用过——如果是首次调用，则 CRLF 问题可能此前未被发现。
3. `eulerpublisher` 包的版本及发布流程，以确认由哪一方负责修复并重发该包。
4. 如果修复权在 `eulerpublisher` 仓库，需确认是否有对应的 Issue/PR 流程来跟踪此缺陷。

## 修复验证要求
无须 code-fixer 对当前 PR 仓库的代码做任何修改。若需修复 `bwa_test.sh` 的 CRLF 问题，应在 `eulerpublisher` 所属仓库中进行，修复后验证 `file bwa_test.sh` 输出不包含 "CRLF" 或 "CR line terminators" 字样。
