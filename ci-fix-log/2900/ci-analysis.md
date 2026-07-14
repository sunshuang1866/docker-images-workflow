# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2依赖缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 在 [Check] 阶段执行容器验证测试时，`common_funs.sh` 脚本第 13 行尝试 source `shunit2`（Shell 单元测试框架），但该框架未安装在 CI Runner 上，导致 Check 步骤报错退出，整个 Pipeline 标记为失败。

### 与 PR 变更的关联
**与 PR 无关。** PR 变更仅新增了 `Others/httpd/2.4.66/24.03-lts-sp4/Dockerfile`、`httpd-foreground` 启动脚本以及相关 README/meta/image-info 元数据更新。Docker 镜像构建（7/7 步骤全部成功）和推送（Push finished）均已完成，失败发生在构建后 CI 自身的 Check 测试框架阶段，属于 CI 基础设施缺少 `shunit2` 依赖。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 上安装 `shunit2` Shell 测试框架。`shunit2` 可通过包管理器（如 `apt-get install shunit2`、`dnf install shunit2`）或从 GitHub 下载安装。安装后重新触发 CI 流水线即可。

### 方向 2（置信度: 低）
如果 CI Runner 环境不可修改，可检查 `eulerpublisher` 测试框架的配置，确认是否存在跳过 Check 阶段的参数或环境变量，在 Runner 层面绕过该步骤（不推荐，会跳过容器验证）。

## 需要进一步确认的点
- 确认 CI Runner 上原本是否应预装 `shunit2`（通常作为 `eulerpublisher` 的依赖），本次缺失是否为 Runner 环境变更或镜像回退导致。
- 查看同一时间段其他 PR 的 CI 是否也出现相同的 `shunit2: file not found` 错误，以确认是否为全局性基础设施问题（而非 PR 特有问题）。
