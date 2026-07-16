# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, eulerpublisher

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed

+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: 无法定位到具体文件（CI 基础设施层面）
- 失败原因: CI [Check] 阶段的测试框架脚本 `common_funs.sh` 尝试加载 `shunit2`（Shell 单元测试框架），但 CI runner 环境中未安装该工具，导致测试无法执行、检查结果为空、Check 被标记为失败。

### 与 PR 变更的关联
与 PR 改动**无关**。Dockerfile 构建和镜像推送均已完成（`#8 DONE 268.4s`、`[Build] finished`、`[Push] finished`），PostgreSQL 从源码编译、安装全程无报错。失败仅发生在 `eulerpublisher` 工具的 [Check] 阶段，原因是 CI runner 缺少 `shunit2` 测试框架依赖。

## 修复方向

### 方向 1（置信度: 高）
属于 CI 基础设施问题，需要 CI 管理员在 runner 节点上安装 `shunit2` Shell 测试框架（如 `dnf install shunit2` 或从 GitHub 获取并加入 PATH）。Code Fixer **无需处理**。

## 需要进一步确认的点
- 确认该 CI runner 上其他镜像的 [Check] 阶段是否也因同样原因失败（若其他镜像通过，则可能是该镜像的测试配置路径缺少 shunit2 依赖声明）
- 检查 `common_funs.sh` 中 `shunit2` 的加载方式（直接 source vs. 从指定路径加载），确定是系统级缺失还是路径配置问题
