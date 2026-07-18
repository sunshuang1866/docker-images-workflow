# 修复摘要

## 修复的问题
CI appstore 发布规范校验工具对 `README.md` 路径比对失败——校验工具期望路径为 `/README.md`，但实际传入路径为 `README.md`，因缺少前导斜杠归一化导致误报。

## 修改的文件
无。在允许修改的文件范围（`README.md`）内，没有需要修复的代码问题。

## 修复逻辑
CI 失败的根本原因是校验脚本 `eulerpublisher/update/container/app/update.py:273` 中的路径比较逻辑未对文件路径做归一化处理（统一添加或去除前导 `/`）。`README.md` 文件本身位于仓库根目录，内容正确无误，无任何需要修改的地方。

由于本 PR 仅修改了 `README.md`，而 CI 校验工具代码不在 `pr.changed_files` 范围内，无法在允许的文件范围内实施修复。该问题需由 CI 维护者在 `update.py` 中增加路径归一化逻辑来解决。

## 潜在风险
无——`README.md` 未做任何修改，不存在引入新问题的风险。