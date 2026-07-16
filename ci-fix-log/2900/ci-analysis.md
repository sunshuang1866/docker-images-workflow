# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺少shunit2
- 新模式症状关键词: shunit2, file not found, eulerpublisher, common_funs.sh, Check

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
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI 测试框架脚本）
- 失败原因: CI 环境中 `eulerpublisher` 容器测试框架在 [Check] 阶段尝试加载 `shunit2` shell 单元测试库时失败，该依赖未安装或路径不可用，导致镜像功能验证测试无法执行。Docker 构建与推送本身均已完成（#10 DONE 41.6s、[Build] finished、[Push] finished）。

### 与 PR 变更的关联
**无关。** PR 变更仅新增了一个 httpd 2.4.66 的 Dockerfile 及配套文件（`httpd-foreground` 入口脚本、`meta.yml` 条目、`README.md` 和 `image-info.yml` 表格行），Docker 镜像构建（configure → make → make install）已完全成功。失败发生在构建完成后的镜像功能检查阶段，`shunit2` 缺失是 CI runner 自身环境问题，与此次 PR 的任何代码变更均无关联。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 包（openEuler 上的包名通常为 `shunit2`），确保 `eulerpublisher` 的容器测试框架能正确定位并加载该库。这不是代码仓层面的修复，而是 CI 基础设施运维问题。

## 需要进一步确认的点
- 确认 CI runner 上 `shunit2` 原本是否已安装—可能是近期 CI 环境变更导致该依赖被移除或版本升级后路径变更。
- 检查同类 CI 流水线中其他镜像的 [Check] 阶段是否也因相同原因失败（以判断是全局性问题还是特定 job 的孤立问题）。
- 由于日志显示的 Check 结果表格为空（无 Check Items 条目），若 `shunit2` 问题修复后仍出现测试失败，需获取该镜像的实际容器测试日志。
