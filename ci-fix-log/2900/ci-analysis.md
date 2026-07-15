# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Check阶段shunit2缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, CRITICAL: [Check] test failed

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
- 失败位置: CI test runner 内置脚本 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 的 `[Check]` 阶段在验证已构建镜像时，测试脚本 `common_funs.sh` 尝试 `source`（`.`）`shunit2`，但 CI runner 环境中未安装 `shunit2`（Bash 单元测试框架），导致测试框架无法启动，Check 阶段直接标记失败。

### 与 PR 变更的关联
与 PR 变更**完全无关**。PR 仅新增了以下文件：
- `Others/httpd/2.4.66/24.03-lts-sp4/Dockerfile`（httpd 2.4.66 的构建和配置）
- `Others/httpd/2.4.66/24.03-lts-sp4/httpd-foreground`（容器启动脚本）
- README.md、image-info.yml、meta.yml 中的条目更新

Docker 镜像构建（`[Build]` 阶段）和推送（`[Push]` 阶段）均成功完成：
```
#10 DONE 41.6s
[Build] finished
[Push] finished
#14 DONE 31.3s
```

失败发生在 CI 流水线自身的 `[Check]` 阶段，由 CI runner 测试环境缺少 `shunit2` 库导致，属于纯基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
CI 管理员在 runner 节点上安装 `shunit2` BASH 单元测试框架。openEuler 仓库中对应的包名通常为 `shunit2` 或可从 EPOL 源安装。安装后重新触发 CI 流水线即可通过。

### 方向 2（置信度: 低）
如果 `shunit2` 包在指定 runner 的 openEuler 版本中不可用，可将其替换为其他 BASH 测试框架或将 Check 逻辑改为独立脚本验证（直接运行 `httpd-foreground` 测试镜像启动）。但这属于 CI 系统层面的改造，超出 PR 贡献者的责任范围。

## 需要进一步确认的点
1. CI runner 上 `shunit2` 的安装路径是否与 `common_funs.sh` 中预期的路径一致（脚本中是否有覆盖 `PATH` 或指定相对路径）
2. 同一批次其他 PR（如其他 httpd 版本同架构）的 Check 阶段是否也因相同原因失败——若存在，可确认是 runner 环境级问题
3. 确认 openEuler 24.03-LTS-SP4 对应的 runner 是否是新部署的节点，可能缺少预装依赖

## 修复验证要求
无需验证——该失败为 infra-error，与 PR 的 Dockerfile 或代码变更无关。CI 管理员修复 runner 环境后重新触发即可。
