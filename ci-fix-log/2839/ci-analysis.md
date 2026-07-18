# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, eulerpublisher, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/common/common_funs.sh`:13
- 失败原因: CI 编排工具 `eulerpublisher` 在 [Check] 阶段执行容器功能测试时，`common_funs.sh` 脚本尝试 source/调用 `shunit2`，但该 shell 测试框架未安装在 CI runner 上，导致测试阶段失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了 PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh、以及更新 README.md 和 meta.yml。Docker 镜像构建和推送均已成功完成：
- `#8 DONE 268.4s` — PostgreSQL 编译和安装成功
- `[Build] finished` — 镜像构建完成
- `[Push] finished` — 镜像推送完成
- `#11 exporting to image ... DONE 58.0s` — 镜像导出/推送完成

失败发生在构建和推送全部成功之后的 [Check] 测试阶段，因 CI runner 缺少 `shunit2` 依赖导致测试框架无法启动。

## 修复方向

### 方向 1（置信度: 高）
**属于 CI 基础设施问题，Code Fixer 无需处理。** 需要在 CI runner 环境中安装 `shunit2` shell 测试框架，或将 `common_funs.sh` 脚本改为从网络动态下载 `shunit2`（与其他项目测试脚本如 `faiss_test.sh`、`snappy_test.sh` 等保持一致的做法——下载至 `/tmp/shunit2_XXXXXX` 后使用）。

## 需要进一步确认的点
1. 确认同一 CI runner 上其他镜像的 [Check] 测试是否也因 `shunit2` 缺失而失败——如果是，说明这是 CI 环境级别的回归问题。
2. 确认 `common_funs.sh` 第 13 行是通过 `source`、`. `（source 的简写）还是直接执行来引用 `shunit2`，以确定是文件不存在还是 PATH 中无此命令。
