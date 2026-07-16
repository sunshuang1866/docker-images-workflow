# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: CI appstore 发布规范预检阶段（`eulerpublisher/update/container/app/update.py:273`）
- 失败原因: CI appstore 预检工具对仓库根目录的 `README.md` 文件触发了路径校验错误，报告"期望路径应为 /README.md"。该文件实际位于 `/README.md`，与期望路径一致，预检工具的路径比较逻辑疑似存在前缀 `/` 的格式化差异或误报。

### 与 PR 变更的关联
**与 PR 变更无关。** PR #3153 仅修改 `README.md` 和 `README.en.md` 两个文件的文档内容（新增 openEuler 24.03-lts-sp4、24.03-lts-sp3、25.09 等基础镜像 Tag 条目），未涉及任何 Dockerfile、元数据文件或镜像目录结构的变更。CI 失败是 appstore 预检工具对根目录文档文件的不当路径校验造成的，属于 CI 基础设施侧问题。

## 修复方向

### 方向 1（置信度: 中）
CI appstore 预检工具（`update.py` 中的路径校验逻辑）存在对仓库根目录非镜像文件的误报问题。建议 CI 维护团队检查 `update.py` 中的路径校验规则，使其在检测到变更文件仅为根目录文档（如 `README.md`）时跳过 appstore 发布规范检查，或修正路径比较时的前导 `/` 处理逻辑。

### 方向 2（置信度: 低）
若此检查并非误报，而是 CI 规范要求 PR 不得同时包含根目录文档变更和镜像目录变更，则 PR 作者可将 README.md 的文档更新与镜像变更拆分为两个独立 PR 提交。但从日志判断，此 PR 仅包含文档变更，方向 1 更符合实际。

## 需要进一步确认的点
1. CI appstore 预检工具（`eulerpublisher/update/container/app/update.py`）中路径校验的具体实现逻辑，确认 `README.md` 与 `/README.md` 的比较失败是否由字符串格式差异导致。
2. 是否存在 CI 配置规则要求 appstore 预检应排除根目录文档文件（如 `README.md`）的变更。
3. 同类 PR（纯文档更新）在该 CI 流水线中的历史表现——是否所有对 `README.md` 的修改都会触发此检查失败。
