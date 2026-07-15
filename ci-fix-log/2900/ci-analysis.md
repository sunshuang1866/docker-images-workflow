# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: CI测试框架依赖缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, eulerpublisher

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
- 失败位置: CI Runner 上的 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: Docker 镜像构建和推送均成功完成（`[Build] finished`、`[Push] finished`），失败发生在 CI 的 `[Check]` 阶段——`eulerpublisher` 测试框架的 `common_funs.sh` 脚本尝试 source `shunit2`（shell 单元测试框架），但 `shunit2` 未安装在 CI Runner 上。由于测试框架本身加载失败，Check Items 表格为空（无任何测试实际执行）。

### 与 PR 变更的关联
PR #2900 新增了 `Others/httpd/2.4.66/24.03-lts-sp4/Dockerfile`、`httpd-foreground` 启动脚本、README.md 和 `image-info.yml` 中对应条目，以及 `meta.yml`，属于标准的镜像新增流程。Docker 构建 7 个步骤全部成功（日志中 `#10 DONE 41.6s`、`#11 DONE 0.1s`、`#12 DONE 0.0s`、`#13 DONE 0.1s`，镜像成功推送到 registry），失败点与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 低）
确认 CI Runner 的测试环境是否安装了 `shunit2`。若 `shunit2` 缺失，在 CI Runner 上安装 `shunit2`（如 `dnf install shunit2` 或从源码部署）后重新触发构建。

### 方向 2（置信度: 低）
检查 `eulerpublisher` 的 `common_funs.sh` 是否正确配置了 `shunit2` 的查找路径（如 `PATH` 或特定目录），可能需要在 CI 环境变量中指定 `SHUNIT2_HOME`。

## 需要进一步确认的点
- `shunit2` 是否已在该 CI Runner 节点上安装（检查 `/usr/local/etc/eulerpublisher/tests/` 下是否有 `shunit2` 文件或软链）
- 同类其他 SP2/SP3 镜像（如已有的 `2.4.66-oe2403sp2`）在同一个 CI Runner 上是否也曾触发相同的 `shunit2: file not found` 错误
- 该 CI 节点是否为新部署的 x86_64 Runner，测试依赖尚未完整安装
