# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-update.py[line:356]-INFO: Difference: [
    "README.md"
]
2026-07-14 15:28:07,685-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范检查工具扫描到 PR 变更了根目录下的 `README.md`，但该文件不符合 appstore 镜像发布所需的路径规范（appstore 发布要求变更文件位于 `{category}/{app-name}/{version}/` 等特定目录结构下，而非仓库根目录）

### 与 PR 变更的关联
PR 仅修改了两个仓库根目录级的文档文件（`README.md` 和 `README.en.md`），更新了其中的 openEuler 版本 tag 列表（新增 25.09、24.03-lts-sp3、24.03-lts-sp2 条目，修正 24.03-lts-sp2 的 URL）。变更未涉及任何 Dockerfile、meta.yml、image-info.yml 或 image-list.yml 等应用镜像必需文件，因此触发了 CI appstore 发布规范校验工具的路径错误。该失败并非由代码错误或构建问题引起，而是 PR 的文件变更范围与 CI 期望的 appstore 镜像发布规范不匹配。

## 修复方向

### 方向 1（置信度: 中）
PR 为纯文档更新（README 版本 tag 列表修正），不涉及任何应用镜像的 Dockerfile 或元数据文件。CI appstore 发布规范检查对本 PR 而言不适用——根目录 README.md 本身就是合法的仓库文档路径。如仍需通过 CI，可考虑：
- 确认本 PR 的 CI trigger 是否应跳过 appstore 发布规范检查（纯文档 PR 不应触发该检查）
- 或确认 README.md 变更是否确实需要纳入 appstore 发布流程，如需纳入则需补充对应的元数据文件

### 方向 2（置信度: 低）
`update.py` 的路径校验逻辑可能对根目录 README.md 存在误判。若工具预期 README.md 必须位于某个镜像子目录内（而非仓库根目录），则属于 CI 工具本身的校验规则需要适配。

## 需要进一步确认的点
1. 本次 CI 触发是否为 `merge_request` 事件自动触发，且未按文件变更类型做过滤（纯文档 PR 理论上不应触发 appstore 发布规范检查）
2. `update.py` 中第 273 行附近的对 README.md 的路径校验逻辑具体是什么——为何文件的绝对路径 `/README.md` 与期望路径 `/README.md` 相同却仍然判定为 FAILURE
3. PR #2512 的 `.claude/README.md` 同类问题（模式11）最终是如何解决的，本 PR 是否可参考同一处理方式
