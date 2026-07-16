# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

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
- 失败位置: CI Runner 的 `eulerpublisher` 测试框架层（`/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`）
- 失败原因: CI Runner 节点缺少 `shunit2`（Shell 单元测试框架），导致容器镜像的 [Check] 验证阶段无法执行。Docker 镜像的构建（[Build] finished）和推送（[Push] finished）均已成功完成，`make -j "$(nproc)" && make install` 编译全过程无报错通过。

### 与 PR 变更的关联
与 PR 代码变更**无关**。PR 新增了 `Database/postgres/17.6/24.03-lts-sp4/Dockerfile`、`entrypoint.sh`，并在 `meta.yml` 和 `README.md` 中补充了新版本条目。Docker 构建全流程（`#8 DONE 268.4s` → `#9 DONE 0.1s` → `#10 DONE 0.1s` → `#11 DONE 58.0s`）顺利完成，PostgreSQL 17.6 源码编译、安装、镜像导出与推送均无异常。失败仅发生在 CI 编排工具 `eulerpublisher` 的容器功能测试阶段，属于 CI 环境缺少测试依赖。

## 修复方向

### 方向 1（置信度: 高）
CI Runner 节点安装 `shunit2`。`shunit2` 是 Shell 单元测试框架，需要被安装到 CI Runner 可见的路径下（`common_funs.sh` 中通过 `source` 或 `PATH` 引用）。联系 CI 基础设施团队在 `eulerpublisher` 测试用的 runner 节点上安装 `shunit2`（可通过 `dnf install shunit2` 或 `pip install shunit2` 等方式）。安装后重新触发 CI 构建，Check 阶段应能正常执行。

### 方向 2（置信度: 低）
如果 CI 基础设施不支持安装 `shunit2`，可考虑调整 `eulerpublisher` 测试逻辑使其不依赖 `shunit2`，或将容器启动测试改为其他验证方式。但这属于 CI 工具链改造范畴，与当前 PR 无关。

## 需要进一步确认的点
1. CI Runner 节点是否有 `shunit2` 包可用的软件源（`dnf search shunit2`），或需以其他方式安装。
2. 同类仓库其他镜像的 Check 测试是否也因同样原因失败——如果其他镜像 Check 能通过，则可能是当前 runner 池中部分节点缺少 `shunit2`。
3. `eulerpublisher` 的 `common_funs.sh` 对 `shunit2` 的具体引用方式（`source` 还是 `PATH` 查找），以确定安装后的路径要求。
