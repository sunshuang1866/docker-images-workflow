# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39
- 新模式标题: (无)
- 新模式症状关键词: (无)

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13（CI 测试框架内部脚本）
- 失败原因: CI 运行环境中 `shunit2`（Shell 单元测试框架）未安装或不在可搜索路径中，导致 `common_funs.sh` 在第 13 行执行 `. shunit2`（source 命令）时报 `file not found`，Check 测试阶段直接崩溃，Check Items 表为空——即没有任何实际测试被执行。

### 与 PR 变更的关联
**与 PR 变更无关。** 证据如下：
- Docker 构建（Step #10 `./configure && make && make install`）全程顺利完成：`#10 DONE 41.6s`
- 构建后处理步骤（Step #11 groupadd/useradd/sed 配置）正常：`#11 DONE 0.1s`
- COPY 和 chmod 步骤均正常：`#12 DONE 0.0s`, `#13 DONE 0.1s`
- 镜像导出和推送成功：`[Build] finished`, `[Push] finished`
- PR 仅新增 Dockerfile、httpd-foreground 启动脚本、README.md 表格行、image-info.yml 表格行、meta.yml 条目，均为纯粹的镜像定义层变更，未触及任何 CI 流水线配置或测试脚本
- 失败发生在 `eulerpublisher` 测试框架内部（`common_funs.sh` 第 13 行），该脚本位于 CI runner 的 `/usr/local/etc/` 系统路径下，属于 CI 基础设施层面

## 修复方向

### 方向 1（置信度: 高）
CI 运维人员需在运行该 Check 流程的 CI runner 环境中安装 `shunit2` Shell 测试框架。`shunit2` 通常可通过系统包管理器安装（如 `dnf install shunit2`）或从 GitHub Release 下载后放入 `PATH`。`common_funs.sh` 脚本期望通过 source 命令（`.`）直接找到 `shunit2`，说明该工具应位于 Shell 的 `PATH` 可搜索路径中。

## 需要进一步确认的点
- `shunit2` 是此前就在该 CI runner 上存在后来丢失，还是该 runner 环境为新建/新配置，从未安装过 `shunit2`？
- 同一 Check 阶段的同类镜像（如其他 httpd 版本 `2.4.66-oe2403sp2`）是否也有同样问题？若同样失败，说明是环境级缺失；若仅当前失败，需排查是否存在条件分支导致 `shunit2` 仅在特定镜像类型才被引用。
- Check Items 表为空，需确认 `shunit2` 修复后测试用例是否能正常通过。
