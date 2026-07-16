# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

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
- 失败位置: CI 测试框架脚本 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI Runner 上缺少 `shunit2`（Shell 单元测试框架）。Docker 镜像构建（`[Build] finished`）和推送（`[Push] finished`）均已成功完成，失败仅发生在 CI 的 `[Check]` 阶段——测试脚本 `common_funs.sh` 在第 13 行尝试 `. shunit2` 加载该测试框架时，`shunit2` 文件不存在于 CI 环境路径中，导致整个测试流程无法启动，检查结果表为空。

### 与 PR 变更的关联
**无关。** PR 所有变更（新增 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、httpd-foreground 启动脚本、meta.yml/README.md/image-info.yml 元数据更新）均正常构建并成功推送镜像。构建步骤 #9（编译 httpd）、#10（安装）、#11（配置 group/user/sed）、#12（COPY 启动脚本）、#13（chmod 可执行权限）全部成功。失败仅发生在 CI 管线的 `[Check]` 测试阶段，属于 CI 基础设施环境依赖缺失问题。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施团队需在运行 `[Check]` 阶段的 Runner 环境中安装 `shunit2` 测试框架（如 `yum install shunit2` 或等效方式）。该工具为 CI 编排工具 `eulerpublisher` 的容器测试脚本 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 所依赖，缺失会导致该 Runner 上所有镜像的 `[Check]` 阶段均无法执行。

## 需要进一步确认的点
- 该 CI Runner 上 `shunit2` 是原本存在但被意外移除，还是该 Runner 是新增节点未完成初始化配置。
- 其他使用同一 Runner（`ecs-build-docker-x86-sp` 或同级节点）的 PR 是否也遇到相同 `shunit2: file not found` 错误，以确认是否为系统性基础设施问题。
- `shunit2` 在 openEuler 24.03 上的包名确认（可能是 `shunit2` 或 `shunit`），以及是否需要从 EPOL 等额外仓库安装。
