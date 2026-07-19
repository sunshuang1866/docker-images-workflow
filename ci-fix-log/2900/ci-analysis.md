# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架shunit2缺失
- 新模式症状关键词: shunit2: file not found, eulerpublisher, [Check] test failed, common_funs.sh

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
- 失败原因: CI 测试编排工具 `eulerpublisher` 的 `[Check]` 阶段在执行容器运行时检查时，`common_funs.sh` 脚本第 13 行 `source`（` .`）了 `shunit2`——一个 shell 单元测试框架，但 `shunit2` 在 CI runner 环境中未安装或不在 `PATH` 中，导致测试脚本无法执行，所有检查项结果为空表，`[Check]` 阶段判定为失败。

### 与 PR 变更的关联
- Docker 镜像的 **构建**（`[Build]`）与 **推送**（`[Push]`）均已成功完成（日志中可见 `[Build] finished`、`[Push] finished`，以及 `#14 DONE 31.3s` 推送成功）。
- PR 变更仅包含：新增 Dockerfile、新增 `httpd-foreground` 启动脚本、更新 `README.md`/`image-info.yml`/`meta.yml` 四个元数据文件。
- `shunit2` 缺失是 CI runner 自身环境问题，与 PR 的代码变更无关。该 PR 的 Dockerfile 构建无任何编译、配置或运行时错误（warnings 中仅有 1 条 `LegacyKeyValueFormat` 格式建议，不导致失败）。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境（或 `eulerpublisher` 的测试依赖）中安装 `shunit2` shell 测试框架。`shunit2` 是一个标准的 sh/Bash 单元测试库，可从 GitHub（`kward/shunit2`）获取。修复后重新触发 CI 即可。

### 方向 2（置信度: 低）
若 `shunit2` 已在环境中安装但路径配置有误，检查 `common_funs.sh` 中 `source`/`.` `shunit2` 的路径是否正确，或检查 `PATH`/`SHUNIT2_HOME` 等环境变量是否指向 `shunit2` 安装位置。

## 需要进一步确认的点
- 确认 `shunit2` 在 CI runner 节点上是否已安装（执行 `which shunit2` 或检查 `/usr/local/etc/eulerpublisher/tests/` 目录下是否存在 `shunit2` 文件）。
- 确认同类仓库其他镜像的 CI 检查（如已有的 httpd 2.4.66-oe2403sp2）是否也触发同样的 `shunit2` 缺失问题——如果是，则说明 runner 环境本身有缺陷，与本次 PR 改动完全无关。

## 修复验证要求
无。此失败为 infra-error，不涉及代码修改，无需 code-fixer 进行补丁、正则匹配或文件修改操作。
