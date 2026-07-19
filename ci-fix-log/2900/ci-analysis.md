# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI检查工具缺shunit2
- 新模式症状关键词: shunit2: file not found, common_funs.sh, [Check] test failed, eulerpublisher

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
- 失败位置: CI Runner 上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 在执行 `[Check]` 阶段的容器验证测试时，其内部脚本 `common_funs.sh` 尝试 source `shunit2`（Shell 单元测试库），但该文件在 CI Runner 上不存在，导致测试框架在启动瞬间直接崩溃。

### 与 PR 变更的关联

**与 PR 改动无关。** 

证据如下：
1. Docker 镜像构建阶段全部成功完成（`#10 DONE 41.6s`、`#11 DONE 0.1s`、`#12 DONE 0.0s`、`#13 DONE 0.1s`），无任何编译错误、运行时错误或退出码非零。
2. 镜像导出和推送均成功（`#14 exporting to image` → `#14 DONE 31.3s`，push 完成）。
3. 唯一的失败点发生在 CI 自身的 `[Check]` 阶段，错误为 `shunit2: file not found`，这是 CI Runner 上 `eulerpublisher` 测试框架缺失依赖库的问题，与本次 PR 新增的 Dockerfile、httpd-foreground 脚本及文档更新无关。

PR 新增的 Dockerfile 中 `yum install` 拉取了 `autoconf make gcc apr apr-devel apr-util-devel pcre-devel`，httpd 2.4.66 成功编译安装，`groupadd`/`useradd` 等运行命令也正常执行。

## 修复方向

### 方向 1（置信度: 高）
CI Runner 上 `eulerpublisher` 测试工具缺少 `shunit2` 依赖。需要在 CI Runner 环境中安装 `shunit2`（如通过 `dnf install shunit2`），或修复 `common_funs.sh` 中 `shunit2` 的 source 路径，使测试框架能正常加载。此问题应由 CI 基础设施团队处理，与 PR 代码无关，Code Fixer 无需对本 PR 的内容做任何修改。

## 需要进一步确认的点

1. 确认 CI Runner 上是否应该预装 `shunit2` 包——对比其他成功通过 `[Check]` 阶段的同类镜像 PR，验证该失败是否为特定 Runner 的偶发环境问题还是系统性问题。
2. 确认 `common_funs.sh` 的 `shunit2` source 路径是否为 `/usr/local/etc/eulerpublisher/tests/container/common/` 下相对路径解析错误，可能需要检查 `eulerpublisher` 版本兼容性。
3. 如果该 Runner 上 `shunit2` 确实已安装但 source 路径不对，则需要排查 `eulerpublisher` 测试框架的打包/部署流程。
