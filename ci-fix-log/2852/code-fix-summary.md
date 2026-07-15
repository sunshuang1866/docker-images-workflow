# 修复摘要

## 修复的问题
修复 `conan config set hooks=bzip2_source_fix` 语法错误导致 Docker 构建在 builder stage 失败的问题。

## 修改的文件
- `Database/milvus/2.6.0/24.03-lts-sp4/Dockerfile`:39: 将无效的 `conan config set hooks=bzip2_source_fix` 替换为直接向 `/root/.conan/conan.conf` 追加写入 hook 配置的 printf 命令。

## 修复逻辑
Conan 1.61.0 的 `conan config set` 命令不接受对整个节（section）赋值，只能使用 `section.key=value` 格式。原命令 `conan config set hooks=bzip2_source_fix` 缺少 `key=value` 格式，CLI 报错 `You can't set a full section, please specify a section.key=value`。

修复方案：改用 `printf '[hooks]\nbzip2_source_fix\n' >> /root/.conan/conan.conf` 直接向 conan.conf 文件追加写入 hook 注册配置，这与 Conan 内部在 conan.conf 中注册 hook 的格式一致，绕过 CLI 的语法限制。

## 潜在风险
无。该修复仅影响 Docker 构建中 conan hook 的注册方式，hook 文件本身（`/root/.conan/hooks/bzip2_source_fix.py`）未做任何修改，功能行为完全一致。sp2 版本的 Dockerfile 未使用该 hook 配置，不影响其他版本。