# 修复摘要

## 修复的问题
Percona Server cmake 构建阶段因缺少 LDAP/SASL/Kerberos 认证开发库而失败。

## 修改的文件
- `Cloud/percona/8.4.8/24.03-lts-sp3/Dockerfile`: 在 `dnf install` 行补充 `openldap-devel`、`cyrus-sasl-devel`、`krb5-devel` 三个包。

## 修复逻辑
CI 分析报告指出 Dockerfile 第 9 行的 `dnf install` 遗漏了 Percona Server 默认 `-DWITH_AUTHENTICATION_LDAP=ON` 所需的三个认证开发库。cmake 警告中明确指出需要安装 `openldap-devel`、`cyrus-sasl-devel`、`krb5-devel`。修复直接将这些包名追加到 `dnf install -y` 命令中，与模式10（缺少构建依赖）完全吻合。

## 潜在风险
- openEuler 24.03-LTS-SP3 仓库中 `cyrus-sasl-devel` 包名可能与 RHEL 略有差异（如 `libsasl2-devel`），若构建仍失败则需调整该包名。
- 三个新增开发库仅影响编译阶段，不会改变最终镜像的运行时行为。