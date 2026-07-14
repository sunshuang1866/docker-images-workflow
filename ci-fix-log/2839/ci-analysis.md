# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架依赖缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh

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
```

### 根因定位
- 失败位置: CI 环境的 `[Check]` 阶段（构建和推送阶段均已完成）
- 失败原因: CI 测试框架 `eulerpublisher` 在执行 `[Check]` 测试时，`common_funs.sh` 尝试 source `shunit2` shell 测试库，但该库在 CI runner 环境中不存在，导致测试框架初始化失败，所有测试项均未执行，Check 表格为空并直接报 `CRITICAL`。

### 与 PR 变更的关联
与 PR 变更 **无关**。Docker 镜像构建（`docker build`）阶段全部成功——configure、make、make install 均正常完成（最终 `#8 DONE 268.4s`），镜像导出和推送（`exporting to image`、`pushing layers`）也全部成功。失败发生在独立的 `[Check]` 阶段，该阶段由 `eulerpublisher` 框架驱动，调用 `common_funs.sh` 执行容器功能测试，而 `shunit2` 是框架的运行时依赖，其缺失属于 CI runner 环境配置问题，与本次 PR 新增的 Dockerfile、entrypoint.sh、meta.yml、README.md 变更无关。

## 修复方向

### 方向 1（置信度: 高）
在负责 `[Check]` 阶段的 CI runner/容器环境中安装 `shunit2` shell 测试框架。`shunit2` 通常以 shell 脚本形式提供，可直接从 GitHub（`https://github.com/kward/shunit2`）下载并放置到 `PATH` 中，或通过包管理器（如 `dnf install shunit2`）安装。若该 runner 环境由 Docker 镜像定义，需在镜像中补充此依赖。

### 方向 2（置信度: 低）
若 `shunit2` 已安装在 runner 环境中但路径不在 `PATH` 内，则需要修正 `common_funs.sh` 中 `source shunit2` 的引用路径，改为 `shunit2` 的实际安装位置。

## 需要进一步确认的点
- 确认 `shunit2` 在 CI runner 容器/主机上的安装状态：运行 `which shunit2` 或 `find / -name "shunit2" 2>/dev/null` 确认该文件是否存在。
- 确认其他镜像（如已存在的 postgres 17.6-oe2403sp2）在相同 CI runner 上 `[Check]` 阶段是否也因同样原因失败——若同样失败，说明是该 runner 环境的统性问题；若单独通过，则需进一步对比 runner 调度差异。
- 确认 `eulerpublisher` 框架的 `common_funs.sh` 在 x86_64 runner 上对 `shunit2` 的预期安装路径。

## 修复验证要求
无。此失败为 CI 基础设施问题，不涉及对仓库中 Dockerfile 或源代码的修改。
