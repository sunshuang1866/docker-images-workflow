# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI 测试框架依赖缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 编排工具 `eulerpublisher` 在 [Check] 测试阶段尝试加载 `shunit2` Shell 测试框架（`source shunit2`），但该框架未安装在 CI Runner 上，导致所有容器检查测试均无法执行，Check 结果表为空，CI 判定构建失败。Docker 镜像本身（7 个步骤）已完整构建并推送成功。

### 与 PR 变更的关联
此次失败与 PR 代码变更**无关**。PR 仅新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、httpd-foreground 启动脚本，以及 README/image-list/meta 元数据更新。Docker 构建全流程（yum 安装依赖 → configure → make → make install → 配置修改 → 镜像导出推送）均在日志中显示成功完成（`#10 DONE 41.6s`, `#11 DONE 0.1s`, `#12 DONE 0.0s`, `#13 DONE 0.1s`, `#14 DONE 31.3s`）。失败仅发生在 CI 基础设施的检查阶段。

## 修复方向

### 方向 1（置信度: 高）
CI Runner 环境缺少 `shunit2` 测试框架。需要在 CI Runner 节点上安装 `shunit2`（或等效包），确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 中的 `source shunit2` 可以找到该库。此修复应在 CI 基础设施层面完成，PR 作者无需修改 Dockerfile 或任何仓库文件。

## 需要进一步确认的点
1. 确认 `shunit2` 是否应作为 `eulerpublisher` 安装脚本的一部分自动安装，还是需要单独手动安装
2. 确认该 CI Runner 节点上的 `eulerpublisher` 版本与其他正常运行的节点是否一致
3. 确认其他近期的 PR 构建是否也遇到了相同的 `shunit2: file not found` 错误，以判断这是单节点问题还是全局环境退化
