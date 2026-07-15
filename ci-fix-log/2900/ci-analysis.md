# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 缺少shunit2测试框架
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

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
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试环境的 `common_funs.sh` 脚本尝试通过 `. shunit2` 加载 `shunit2` shell 单元测试框架，但该框架未安装在 CI runner 上，导致 `[Check]` 测试阶段无法执行。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、辅助脚本（httpd-foreground）及元数据文件（README.md、image-info.yml、meta.yml）。Docker 镜像的构建和推送阶段均已完成并成功（`[Build] finished`, `[Push] finished`），失败发生在 CI 后处理/验证阶段，因 CI runner 缺少 `shunit2` 包导致测试框架加载失败。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2`（开源 shell 单元测试框架）。openEuler 24.03-LTS-SP4 仓库中应提供 `shunit2` 包（软件包名通常为 `shunit2`），可通过 `dnf install shunit2 -y` 安装。

## 需要进一步确认的点
- 确认 CI runner 节点的操作系统版本及 `shunit2` 是否在对应的 yum/dnf 源中可用。
- 确认 `eulerpublisher` 测试工具链是否允许将 `shunit2` 作为预装依赖添加到 CI 环境初始化脚本中。
- 如果是临时性的 runner 环境问题（如新节点未完成初始化），可尝试在相同架构的其他 runner 上重试。
