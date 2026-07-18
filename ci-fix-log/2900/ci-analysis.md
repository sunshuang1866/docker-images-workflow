# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39（CI工具依赖缺失）
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
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
- 失败位置: eulerpublisher CI 工具 [Check] 阶段，文件 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI runner 上缺少 `shunit2`（Shell 单元测试框架），eulerpublisher 的容器后构建检查（Check）阶段在初始化测试框架时无法 source 该依赖文件，导致所有容器测试项均未执行（检查结果表为空）。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像构建（7/7 步骤全部 DONE）和推送均已完成：
- `#10 DONE 41.6s` — make + make install 成功
- `#11 DONE 0.1s` — groupadd/useradd/sed 配置均成功
- `#12 DONE 0.0s` — COPY httpd-foreground 成功
- `#13 DONE 0.1s` — chmod 成功
- `#14 DONE 31.3s` — 镜像导出并推送至 registry 成功

失败仅发生在 eulerpublisher 工具的 [Check] 后处理阶段，属于 CI 基础设施问题，与 Dockerfile 或新增文件无关。

（附注：构建过程中有一个 BuildKit 风格警告 `LegacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format (line 5)`，指向 `ENV HTTPD_PREFIX /usr/local/apache2` 写法，但这是非致命警告，不影响构建结果。）

## 修复方向

### 方向 1（置信度: 高）
这是 CI 基础设施问题，**Code Fixer 无需对 PR 代码做任何修改**。需由 CI 运维人员处理：
- 检查该 CI runner 上 `shunit2` 是否已安装。若 `shunit2` 为 RPM 包，执行 `rpm -q shunit2` 确认；若未安装，安装 `shunit2` 即可。
- 若该 runner 为新架构/新环境（如 24.03-LTS-SP4 对应的构建节点），可能尚未完成完整的 CI 环境初始化，需补充安装 shunit2 依赖。

## 需要进一步确认的点
- 确认同一 CI 环境中其他 SP4 镜像（如模式39 涉及的 PR）的 [Check] 阶段是否也有相同的 `shunit2: file not found` 问题，以判断是否为该 runner 的普遍性缺失。
