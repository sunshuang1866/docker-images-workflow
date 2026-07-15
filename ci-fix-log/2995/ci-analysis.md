# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本含CRLF
- 新模式症状关键词: bad interpreter, No such file or directory, ^M, test failed, Check

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 工具 eulerpublisher 自带的测试脚本，非 PR 中文件）
- 失败原因: `eulerpublisher` 发行包中的 `bwa_test.sh` 使用了 Windows 风格换行（CRLF），shebang 行 `#!/bin/sh\r` 中的回车符 `^M` 导致系统无法找到正确的解释器 `/bin/sh\r`（系统实际存在的是 `/bin/sh`，不含 `\r`），bash 报错 "bad interpreter: No such file or directory"。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 的 Docker 镜像构建与推送均已成功完成：
- Dockerfile `#7 [2/2] RUN` 全程正常执行（yum 安装 → 源码下载 → `make` 编译 → 产物安装 → yum 清理，全部通过）
- `#7 DONE 199.0s` 构建层完成
- `#8 DONE 8.4s` 镜像导出并推送成功
- 日志明确记录 `[Build] finished` 和 `[Push] finished`

失败仅发生在 CI 后置的 `[Check]` 阶段，该阶段调用的 `bwa_test.sh` 是 `eulerpublisher` 工具包自带文件，其 CRLF 换行符问题是 CI 基础设施缺陷，与 PR 提交的 Dockerfile、meta.yml、image-info.yml、README.md 无任何关联。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施维护者需要在 `eulerpublisher` 源码仓库中将 `tests/container/app/bwa_test.sh` 的换行符从 CRLF 转换为 LF（`dos2unix` 或 `sed -i 's/\r$//'`），并重新发布 eulerpublisher 包。此问题由 eulerpublisher CI 工具引入，Code Fixer 无需对 PR 代码做任何修改。

## 需要进一步确认的点
- `eulerpublisher` 源码仓库中是否仅有 `bwa_test.sh` 存在 CRLF 问题，还是 `tests/container/app/` 目录下其他测试脚本也受同样影响。
- CI 节点上的 eulerpublisher 版本是否需要回滚到之前不含此缺陷的版本。

## 修复验证要求
Code Fixer 无需处理。此失败与 PR 提交的代码变更完全无关，属于 CI 基础设施工具 eulerpublisher 的测试脚本换行符格式缺陷。
