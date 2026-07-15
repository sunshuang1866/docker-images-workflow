# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本含Windows换行
- 新模式症状关键词: `^M`, `bad interpreter`, `CRLF`, `No such file or directory`

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher 包中的测试脚本）
- 失败原因: `bwa_test.sh` 测试脚本的 shebang 行包含 Windows 风格换行符（CRLF），导致内核将 `/bin/sh\r`（含回车符 `^M`）解析为解释器路径，因该路径不存在而拒绝执行

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了以下文件：
- `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（Docker 镜像构建 100% 成功，199 秒完成）
- `HPC/bwa/README.md`
- `HPC/bwa/doc/image-info.yml`
- `HPC/bwa/meta.yml`

Docker 映像构建（Build + Push）均成功完成，失败发生在 CI 后置的 `[Check]` 阶段——`eulerpublisher` 测试框架调用 `bwa_test.sh` 脚本对已构建好的镜像做功能验证时，因该测试脚本本身包含 CRLF 字符而无法被内核执行。

## 修复方向

### 方向 1（置信度: 高）
此问题属于 CI 基础设施的 `eulerpublisher` 包缺陷：`bwa_test.sh` 文件被以 CRLF 行尾格式打包。需在 `eulerpublisher` 源码仓库中修复该测试脚本的行尾格式（`dos2unix` 或编辑器设置为 LF），并重新发布/部署该包到 CI 节点。PR 的代码变更无需任何修改。

## 需要进一步确认的点
- 确认 `eulerpublisher` 包中 `bwa_test.sh` 的原始行尾格式（在 eulerpublisher 源码仓库中检查该文件）
- 确认是否有其他镜像的测试脚本也存在同样的 CRLF 问题（预防性排查）
- 确认 `eulerpublisher` 包的最新版本是否已修复此问题——若已修复，仅需在 CI 节点更新该包即可
