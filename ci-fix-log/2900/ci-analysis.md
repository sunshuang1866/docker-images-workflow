# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架缺少shunit2
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI runner 上 `eulerpublisher` 测试框架的 `common_funs.sh` 脚本尝试通过 `. shunit2` 命令 source `shunit2`（Shell 单元测试库），但该文件在 runner 环境中不存在或不在预期路径，导致整个 [Check] 阶段无法执行，所有测试项结果为空表。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像的构建、安装、导出、推送全部成功（所有 `#10`～`#14` 步骤均标记 `DONE`，日志中有明确的 `[Build] finished` 和 `[Push] finished` 信息）。失败发生在 `eulerpublisher` 工具的 [Check] 测试框架初始化阶段，属于 CI 基础设施层面的问题，与本次 PR 新增的 Dockerfile、httpd-foreground 脚本、README/meta/image-info 元数据更新均无关联。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 的 `eulerpublisher` 测试环境中安装或恢复 `shunit2` Shell 测试库。`common_funs.sh:13` 使用 `. shunit2` 裸文件名 source，意味着 `shunit2` 应在 `PATH` 中或与 `common_funs.sh` 同目录。需在 CI runner 初始化脚本中确保 `shunit2` 位于 `/usr/local/etc/eulerpublisher/tests/container/common/` 目录下，或将其安装到系统 PATH 可搜索的路径。

## 需要进一步确认的点
- `shunit2` 文件在 CI runner 上的原有路径和安装方式（是通过包管理器安装、手动放置、还是打包在 `eulerpublisher` RPM 中）。
- 该问题是仅影响本次 httpd 构建的 runner 节点，还是所有 `eulerpublisher` 测试节点均受影响——需确认是否需要运维侧修复 CI runner 环境而非修改代码仓库。
