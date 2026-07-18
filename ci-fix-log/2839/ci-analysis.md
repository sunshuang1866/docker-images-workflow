# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: Check阶段shunit2缺失
- 新模式症状关键词: `shunit2: No such file or directory`, `common_funs.sh`, `[Check] test failed`

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: CI 流水线 `[Check]` 阶段，测试脚本 `common_funs.sh:13`
- 失败原因: CI runner 上未安装 shell 单元测试框架 `shunit2`，测试脚本 `common_funs.sh` 在第 13 行尝试加载/引用 `shunit2` 时失败，导致 `[Check]` 阶段整体失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 新增了 postgres 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh 以及相关的 README/meta.yml 更新。Docker 镜像构建和推送均已成功完成（`[Build] finished`, `[Push] finished`），失败仅发生在 CI 测试验证 (`[Check]`) 阶段，且报错为测试框架 `shunit2` 缺失，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 中）
在 CI runner 上安装 `shunit2` 测试框架。shunit2 是一个广泛使用的 Bash 单元测试框架，可通过以下方式在 openEuler 上安装：
- 从 EPOL 仓库安装 `shunit2` RPM 包
- 或从 GitHub 下载 shunit2 脚本到 CI runner 的 PATH 目录中

安装后重新触发 CI 流水线验证 Check 阶段能否通过。

### 方向 2（置信度: 低）
如果 `shunit2` 已正确安装但 PATH 配置有问题，检查 CI runner 上 `common_funs.sh` 脚本引用 `shunit2` 的方式（是否依赖 hardcoded 路径），确认 `shunit2` 的实际安装路径与脚本期望路径一致。

## 需要进一步确认的点
1. 确认该 CI runner 节点上 `shunit2` 的实际安装状态：`which shunit2` 或 `rpm -qa | grep shunit2`
2. 确认该 runner 上的其他镜像 Check 阶段是否也因同样原因失败（可作为对照组）
3. 确认 `common_funs.sh` 第 13 行引入 `shunit2` 的具体方式（是 `source` 还是直接执行，依赖 PATH 还是 hardcoded 路径）

## 修复验证要求
本失败为 infra-error，与 PR 代码变更无关，Code Fixer 无需处理 Dockerfile 或构建逻辑。
