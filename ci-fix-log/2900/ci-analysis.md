# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI测试工具缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, [Check] test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 的 `eulerpublisher` 测试框架在执行 `[Check]` 阶段时，`common_funs.sh` 脚本第 13 行尝试加载 `shunit2` shell 测试库，但该库在 CI runner 环境中未安装或不在 `PATH` 中，导致所有检查项均无法执行（检查结果为空白表），最终 `eulerpublisher` 以 CRITICAL 级别报 `[Check] test failed`。

### 与 PR 变更的关联
与 PR 代码变更**无关**。Docker 镜像的构建和推送均已成功完成：
- `[Build] finished`（构建成功，#10 DONE 41.6s）
- `[Push] finished`（推送成功，#14 DONE 31.3s）
- 仅 `[Check]` 阶段因 CI 环境中 `shunit2` 工具缺失而失败。

该失败为 CI 基础设施问题，PR 新增的 Dockerfile、httpd-foreground 脚本以及 README.md / image-info.yml / meta.yml 的文档更新均未触发编译错误或运行时错误。

## 修复方向

### 方向 1（置信度: 低）
在 CI runner 环境中安装 `shunit2` shell 测试框架（通常可通过包管理器安装，如 `dnf install shunit2` 或从 GitHub 获取脚本放置到 `/usr/local/etc/eulerpublisher/tests/container/common/` 可寻址路径下）。

### 方向 2（置信度: 低）
检查 CI runner 的测试框架 `eulerpublisher` 的部署流程，确认 `shunit2` 是否在 `requirements.txt` 或安装脚本中已声明但实际未安装，补充对应的安装步骤。

## 需要进一步确认的点
- `shunit2` 是 CI runner 环境预期应预装的工具还是仅某些特定镜像类型需要。如果其他已有 HTTPD 镜像（如 24.03-lts-sp2 版本）在同 runner 上 `[Check]` 成功，说明 `shunit2` 应已安装但当前 runner 环境存在配置漂移。
- 需确认触发该 PR 构建的 Jenkins node 标签，检查该 node 上的测试依赖是否完整。
- 可对比同类 HTTPD 镜像（如 `2.4.66/24.03-lts-sp2`）在同一 CI 周期内的 `[Check]` 执行结果，确认是全局 runner 问题还是仅本次构建实例的问题。
