# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher` 测试框架内 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 的 [Check] 阶段在执行容器镜像验证测试时，`common_funs.sh` 第 13 行尝试 source `shunit2` 测试框架，但 CI runner 环境中未安装该依赖，导致所有测试项无法执行（Check Results 表格完全为空），整个 job 判定为失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增 4 个文件：
- `Database/postgres/17.6/24.03-lts-sp4/Dockerfile`（34 行，全新文件）
- `Database/postgres/17.6/24.03-lts-sp4/entrypoint.sh`（362 行，全新文件）
- `Database/postgres/README.md`（新增 1 行表格条目）
- `Database/postgres/meta.yml`（新增 2 行版本条目）

Docker 构建阶段全部成功：
- postgres 17.6 源码编译和 `make install` 完整通过（`#8 DONE 268.4s`）
- COPY entrypoint.sh 成功（`#9 DONE 0.1s`）
- chmod 成功（`#10 DONE 0.1s`）
- 镜像导出和推送成功（`[Build] finished`，`[Push] finished`）

失败仅发生在 `eulerpublisher` 框架的 [Check] 后处理阶段，属于 CI runner 基础设施层面的 `shunit2` 依赖缺失，与 PR 代码无关。

## 修复方向

### 方向 1（置信度: 高）
CI runner 环境缺少 `shunit2` 测试框架。需要在 CI runner 镜像或节点配置中安装 `shunit2`（例如从 `https://raw.githubusercontent.com/kward/shunit2/master/shunit2` 下载到 `/usr/local/bin/` 或 CI 测试框架的预期路径），或者确保 `eulerpublisher` 包安装时自动拉取其测试依赖。本仓库的项目本地测试脚本（如 `tests/hnswlib/hnswlib_test.sh`、`tests/snappy/snappy_test.sh` 等）均使用 `download_shunit2()` 函数动态从 GitHub 下载 shunit2，但 `eulerpublisher` 内置的 `common_funs.sh` 直接 source `shunit2` 而不做动态下载，说明其设计上假定 runner 已预装该依赖。

## 需要进一步确认的点
1. `eulerpublisher` 包的安装文档或 CI runner 初始化脚本中是否声明了 `shunit2` 为必需依赖，当前 runner 环境中该文件是否存在（检查 `/usr/local/bin/shunit2`、`/usr/local/etc/eulerpublisher/tests/container/common/shunit2` 等预期路径）
2. `eulerpublisher` 版本的 `common_funs.sh` 第 13 行具体是 `. shunit2` 还是 `source shunit2`，以及其搜索路径（PATH 相对引用还是硬编码绝对路径）
3. 其他同类镜像的 CI [Check] 阶段是否也遇到相同错误（若普遍存在，说明 CI runner 配置有全局缺陷；若仅此 PR 触发，需排查 runner 调度或环境变量差异）
