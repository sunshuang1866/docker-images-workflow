# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: `shunit2: file not found`, `common_funs.sh`, `[Check] test failed`

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
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
- 失败位置: `eulerpublisher` 测试框架 `common_funs.sh:13`
- 失败原因: CI 运行器上 `eulerpublisher` 测试框架的 `common_funs.sh` 脚本尝试通过 `. shunit2` 加载 shell 单元测试库 `shunit2`，但该文件在系统中不存在或不在搜索路径内，导致 [Check] 阶段无法初始化测试用例，check 结果表为空，整个 job 被标记为失败。

### 与 PR 变更的关联
Docker 镜像构建本身**完全成功**——所有 7 个 RUN/COPY 步骤均正常通过（`#10 DONE 41.6s`, `#11 DONE 0.1s`, ..., `#14 DONE 31.3s`），镜像已成功构建并推送到仓库。失败发生在构建完成之后的 **[Check] 测试验证阶段**，属于 CI 基础设施（测试框架 `shunit2` 缺失）的问题，与 PR 中的 Dockerfile、httpd-foreground、meta.yml、README.md、image-info.yml 变更均无直接因果关系。

日志中唯一的构建期警告（`LegacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format (line 5)`）为非致命提示，不影响构建结果。

## 修复方向

### 方向 1（置信度: 中）
这是一个 CI 基础设施问题——`shunit2` shell 测试库在运行 eulerpublisher [Check] 阶段的 CI 节点上缺失。需要运维/CI 管理员在相关 runner 上安装 `shunit2`（如通过 `dnf install shunit2` 或将其脚本放入 `PATH`），或重新触发构建以确认是否为一过性环境问题。

### 方向 2（置信度: 低）
如果 `shunit2` 确实已在 runner 上安装但路径配置有误，检查 `common_funs.sh` 中 `shunit2` 的加载路径与环境变量 `PATH` 设置是否匹配。

## 需要进一步确认的点
1. 同一 CI runner 上其他镜像的 [Check] 阶段是否也因 `shunit2: file not found` 失败——若所有镜像均失败，则确认为基础设施全局问题；若仅 httpd 失败，需检查 `eulerpublisher` 对该镜像的测试调度逻辑。
2. `shunit2` 在 CI runner 上的预期安装路径及 `common_funs.sh` 中引用的相对/绝对路径。
3. 此 CI runner 的历史日志，确认 `shunit2` 是新近缺失还是持续缺失。
