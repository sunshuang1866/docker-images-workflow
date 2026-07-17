# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 CI测试框架缺失
- 新模式症状关键词: `shunit2: file not found`, `[Check] test failed`, `common_funs.sh`

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI runner 上未安装 `shunit2`（Shell 单元测试框架），导致 [Check] 阶段的容器验收测试脚本无法加载依赖，测试框架初始化失败，检查表格为空（无任何检查项实际执行）。

### 与 PR 变更的关联
**无关。** Docker 镜像构建（所有 7 个步骤）和推送均已成功完成（日志中 `[Build] finished`、`[Push] finished`、镜像 manifest 推送成功）。失败发生在 CI 编排层 `eulerpublisher` 的 [Check] 阶段，原因是 CI runner 主机上缺少 `shunit2` 包。PR 仅新增 Dockerfile、httpd-foreground 脚本和元数据文件（README.md、image-info.yml、meta.yml），未修改 CI 基础设施。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 镜像或构建环境中安装 `shunit2` 包。openEuler 上对应的包名可能为 `shunit2` 或 `epel-release` 后再安装。需联系 CI 基础设施团队排查该 runner 节点的软件包清单。

### 方向 2（置信度: 低）
如果 `shunit2` 确实已安装但路径不在 `PATH` 中，需在 `eulerpublisher` 的测试启动脚本中修正 `shunit2` 的 source 路径。

## 需要进一步确认的点
1. `shunit2` 在 openEuler 24.03 上的确切包名（`dnf search shunit2`）。
2. 该 CI runner 节点上 `shunit2` 是否已安装以及安装路径（`find / -name shunit2 2>/dev/null`）。
3. 对比同一 CI 流水线中成功通过 [Check] 阶段的其他 PR 的 runner 环境，确认是否为特定 runner 节点的问题。
