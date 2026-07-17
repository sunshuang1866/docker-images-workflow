# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39（变体）
- 新模式标题: —
- 新模式症状关键词: —

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896 INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 编排工具 `eulerpublisher` 在执行 `[Check]` 阶段时，其测试框架依赖的 `shunit2` shell 测试库在 CI runner 上不存在，导致测试无法启动，Check 结果表为空，整体流水线标记为失败。

### 与 PR 变更的关联
**无关。** PR 变更仅新增 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件（`httpd-foreground`、`meta.yml`、`README.md`、`image-info.yml`）。Docker 构建阶段（`#9` 源码编译 → `#14` 推送镜像）**全部成功完成**，镜像 `httpd:2.4.66-oe2403sp4-x86_64` 已成功构建并推送到 registry。失败发生在构建和推送完成之后的 `[Check]` 阶段，根因是 CI runner 环境缺少 `shunit2` 测试框架，与本次 PR 的代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题：需在 CI runner 上安装 `shunit2` 测试框架，使 `eulerpublisher` 的 Check 阶段能够正常加载测试脚本。检查 CI runner 环境中 `shunit2` 是否已安装于 `/usr/local/etc/eulerpublisher/tests/container/common/` 或其他期望路径，或在 `common_funs.sh` 中修正 `shunit2` 的 source 路径。**本次 PR 无需修改。**

## 需要进一步确认的点
- CI runner 上 `shunit2` 的预期安装路径是否为 `/usr/local/etc/eulerpublisher/tests/container/common/shunit2`。
- 该 runner 上其他镜像的 Check 阶段是否也因同样的 `shunit2` 缺失而失败（若是，则为系统性 CI 环境问题而非本次 PR 特例）。
- 确认 `shunit2` 是否应随 `eulerpublisher` 包一起安装，还是需要单独安装。
