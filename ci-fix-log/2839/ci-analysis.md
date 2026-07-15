# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失shunit2
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI [Check] 阶段的测试脚本 `common_funs.sh` 尝试加载 `shunit2` 测试框架，但该框架未安装在 CI runner 上，导致测试脚本无法执行。

### 与 PR 变更的关联
PR 变更仅新增了 postgres 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh，以及更新 meta.yml 和 README.md。Docker 镜像构建全程成功（`#8 DONE 268.4s`），源码编译（PostgreSQL 17.6 从源码 `./configure && make && make install`）和镜像推送（`[Push] finished`）均顺利完成。失败发生在 CI 流水线的 [Check] 测试验证阶段，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 中）
在 CI runner 上安装 `shunit2` 测试框架。`shunit2` 是 Shell 脚本单元测试框架，需通过包管理器安装（如 `dnf install shunit2` 或 `pip install shunit2`）。该问题是 CI 基础设施依赖缺失，与 PR 本身的 Dockerfile / entrypoint.sh 代码无关。

### 方向 2（置信度: 低）
如果 `shunit2` 不可通过包管理器直接获取，可在 CI 构建脚本中添加从 GitHub 拉取 shunit2 源码并配置路径的逻辑（shunit2 是一个单文件 Shell 库，可从 https://github.com/kward/shunit2 获取）。

## 需要进一步确认的点
1. 同仓库其他镜像（如 `Database/postgres/17.6/24.03-lts-sp2/Dockerfile`）的 CI 构建是否也出现了同样的 `shunit2: No such file or directory` 错误？如果其他镜像的 [Check] 阶段也失败，则可确认是 CI runner 环境问题。
2. 该 CI runner 上 `shunit2` 是否应该已经预装？如果之前成功运行过 [Check] 测试但现在失败，可能是 runner 环境发生变更（镜像更新、包被意外移除）。
3. 需要获取 CI runner 的环境信息（操作系统版本、已安装包列表），确认 `shunit2` 的安装状态和正确的安装方式。
