# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, [Check] test failed

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
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 在执行 [Check] 阶段时，`common_funs.sh` 尝试通过 `. shunit2` 加载 shell 单元测试框架 shunit2，但 CI 运行环境中未安装该依赖，导致测试脚本立即终止。Docker 镜像的构建（configure → make → make install）和推送到注册表均已成功完成，失败仅发生在 CI 测试基础设施层面。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了以下文件：
- `Others/httpd/2.4.66/24.03-lts-sp4/Dockerfile`（httpd 构建 Dockerfile）
- `Others/httpd/2.4.66/24.03-lts-sp4/httpd-foreground`（容器入口脚本）
- README.md、image-info.yml、meta.yml 的文档/注册更新

Docker 构建全流程（步骤 #4 源码编译 make、步骤 #5 配置修改 sed、步骤 #7 chmod、#14 导出并推送）均成功完成。`shunit2: file not found` 是 CI Runner 环境缺少测试框架依赖的典型基础设施故障，与本次新增的 httpd Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施团队需在 `eulerpublisher` 测试 Runner 环境中安装 `shunit2` shell 测试框架（通常通过包管理器安装 `shunit2` 或设置 `SHUNIT2` 环境变量指向其安装路径）。此问题属于 CI 运维层面，Code Fixer 无需处理 PR 代码。

## 需要进一步确认的点
- 确认 CI Runner 镜像中是否已安装 `shunit2` 包。可通过 `rpm -q shunit2` 或 `which shunit2` 在 Runner 环境中验证。
- 确认 shunit2 的安装路径是否已在 `common_funs.sh` 或 CI 环境变量中正确配置（如 `SHUNIT2` 环境变量或 `PATH`）。
- 确认同一批次的其他 PR（同版本的 openEuler 24.03-LTS-SP4 镜像）在 [Check] 阶段是否也出现相同错误，以判断是全局 Runner 问题还是本 PR 的调度节点问题。
