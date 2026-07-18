# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-.../update.py[line:356]-INFO: Difference: [
    "README.md"
]
...
2026-07-14 15:28:07,685-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.

+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检工具检测到 `README.md` 的路径不符合预期格式（期望 `/README.md`，但 diff 中提取的路径格式可能为 `README.md`，缺少前导 `/`，导致严格字符串匹配失败）

### 与 PR 变更的关联
PR 仅修改了两个 README 文档文件（`README.md` 和 `README.en.md`），更新了可用镜像 Tags 列表（添加 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目，修正 `latest` 标记指向 `sp3`）。这些是纯文档修改，不涉及任何 Dockerfile、构建脚本或元数据文件。CI 失败并非由 PR 内容错误引起，而是 CI 工具 `update.py` 在 appstore 发布规范预检阶段的路径校验逻辑对 `README.md` 的路径表示格式（有无前导 `/`）进行了严格匹配，导致误报。

值得注意的是，CI 的 diff 检测只识别到 `README.md`（未列出 `README.en.md`），说明检查工具可能只对白名单内的文件进行路径校验。

## 修复方向

### 方向 1（置信度: 中）
CI 检查工具 `update.py` 中路径比较可能存在前导 `/` 不一致的问题——diff 输出路径格式（如 `README.md`）与 appstore 规范期期望格式（如 `/README.md`）不匹配。修復方向是让 CI 维护者在 `update.py` 中增加路径归一化逻辑（如统一添加或去除前导 `/` 后再比较），使其对根目录文件路径的两种表示形式均能正确校验。

### 方向 2（置信度: 低）
如果 CI 工具依赖某个配置文件（如 `image-list.yml` 或 appstore schema）来定义允许修改的文件路径，而该配置中 `README.md` 的条目写的是 `/README.md`（带前导 `/`），则原因可能是配置条目与工具从 git diff 提取的路径格式不兼容。修復方向是统一路径格式约定。

## 需要进一步确认的点
1. 需要查看 `eulerpublisher/update/container/app/update.py` 中第 273 行附近的路径校验逻辑，确认是否对路径进行了前导 `/` 的归一化处理。
2. 需要确认 `README.en.md` 是否在 CI 检查的白名单中——若不在，为何未触发该文件的路径校验失败。
3. 是否同样的问题在仅修改 `README.md` 的其他历史 PR 中也存在，以排除环境性因素。
