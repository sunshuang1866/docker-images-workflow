# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架依赖缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI [Check] 阶段 — eulerpublisher 测试框架 `common_funs.sh` 第 13 行
- 失败原因: CI 运行环境缺少 `shunit2`（Shell 单元测试框架），导致镜像的 [Check] 验证脚本无法执行

### 与 PR 变更的关联
与 PR 变更**无关**。Docker 镜像构建和推送均已完成（日志中 `[Build] finished` 和 `[Push] finished` 均确认成功），失败发生在构建后 CI 内置的镜像验证测试（[Check] 阶段），本质是 CI runner 环境缺少 `shunit2` 测试工具。

PR 的改动仅涉及：
1. 新增 Go 1.25.6 × openEuler 24.03-LTS-SP4 的 Dockerfile
2. README.md 和 image-info.yml 中补充版本条目
3. meta.yml 中新增版本-路径映射

以上均为常规新增内容，不涉及任何有可能影响 CI 测试框架配置的修改。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 测试框架。`shunit2` 是 eulerpublisher 容器镜像验证流程的必需依赖，可通过以下方式之一解决：
- 在 CI runner 的基础镜像/环境中预先安装 shunit2 包
- 若 shunit2 的安装路径已存在但 PATH 或 source 路径不正确，修正 `common_funs.sh` 中的引用路径

### 方向 2（置信度: 低）
若 CI 架构近期将 Check 步骤从 shunit2 迁移到了其他测试框架，但旧引用未清理，则需更新 `common_funs.sh` 以适配新框架。

## 需要进一步确认的点
1. CI runner 上是否安装了 shunit2？可执行 `which shunit2` 或检查 `/usr/share/shunit2/` 等常见安装路径
2. 该 runner 上其他 PR 的 [Check] 阶段是否也出现同样的 `shunit2: No such file or directory` 错误——若是，则确认为全局 infra 问题，与 PR 无关
3. CI 团队的 eulerpublisher 部署文档中是否将 shunit2 列为必需依赖；若缺失，需补充安装说明
