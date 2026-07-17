# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

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
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI [Check] 阶段执行容器镜像检查测试时，测试框架脚本 `common_funs.sh` 尝试通过 `.` (source) 加载 `shunit2` 单元测试库，但 CI runner 环境中未安装 `shunit2`，导致测试脚本无法运行，所有检查项均为空，最终 `eulerpublisher` 报告 `[Check] test failed`。

### 与 PR 变更的关联
**与 PR 变更无关**。Docker 镜像的构建（[Build]）和推送（[Push]）阶段均已成功完成：
- Docker 构建所有步骤（#1~#13）均正常完成，#10（configure/make/make install）耗时 41.6s 但成功
- 镜像成功导出并推送到 registry，sha256 manifest 已生成
- 构建日志中唯一的 warning 是 Docker BuildKit 对 `ENV key value` 格式的 `LegacyKeyValueFormat` 建议，不影响构建结果

PR 新增的 Dockerfile 构建本身没有问题。失败发生在构建完成后的镜像检查测试阶段，CI runner 环境缺少 `shunit2` 工具。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境或检查容器中安装 `shunit2` 单元测试框架。openEuler 仓库中包名通常为 `shunit2`，可通过 `dnf install shunit2 -y` 安装。此为 CI 基础设施问题，不需要修改 Dockerfile 或任何 PR 代码。

### 方向 2（置信度: 低）
如果 openEuler 24.03-LTS-SP4 的 `shunit2` 包名或路径与现有版本不同，`common_funs.sh` 中的路径引用可能需要适配新环境。但此可能性较低，`shunit2: file not found` 更可能是包未安装导致。

## 需要进一步确认的点
1. CI runner 基镜像中是否预装了 `shunit2` 包；若曾预装但现在缺失，需确认是否因 runner 环境升级导致包被移除
2. 同仓库其他使用 `eulerpublisher` [Check] 阶段的 PR 是否也遇到相同问题（以判断是全局 runner 问题还是特定于 openEuler 24.03-LTS-SP4 基镜像的问题）

## 修复验证要求
无。此问题为 CI 基础设施缺少 `shunit2` 包，不涉及对 Dockerfile 或任何源代码文件的修改，code-fixer 无需进行正则匹配验证。
