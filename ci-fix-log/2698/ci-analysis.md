# CI 失败分析报告

## 基本信息
- PR: #2698 — Feat: add percona 8.4.8 docker image on openEuler 24.03-LTS-SP3
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式10
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
CMake Error at CMakeLists.txt:2028 (MESSAGE):
  -DWITH_AUTHENTICATION_LDAP=ON, but missing system libraries

-- Configuring incomplete, errors occurred!
CMake Warning at cmake/ldap.cmake:38 (MESSAGE):
  Cannot find LDAP development libraries.  You need to install the required
  packages:
    RedHat/Fedora/Oracle Linux: yum install openldap-devel

CMake Warning at cmake/sasl.cmake:68 (MESSAGE):
  Cannot find SASL development libraries.  You need to install the required
  packages:
    RedHat/Fedora/Oracle Linux: yum install cyrus-sasl-devel cyrus-sasl-scram

CMake Warning at cmake/kerberos.cmake:50 (MESSAGE):
  Cannot find KERBEROS development libraries.  You need to install the
  required packages:
    RedHat/Fedora/Oracle Linux: yum install krb5-devel
```

### 根因定位
- 失败位置: `Database/percona/8.4.8/24.03-lts-sp3/Dockerfile:9`（`dnf install` 行）
- 失败原因: Dockerfile 的 `dnf install` 步骤遗漏了 Percona Server cmake 配置必需的三个认证相关开发库：`openldap-devel`、`cyrus-sasl-devel`、`krb5-devel`，Percona Server 默认启用 `-DWITH_AUTHENTICATION_LDAP=ON`，cmake 检测到这些库缺失后报硬错误终止配置。

### 与 PR 变更的关联
直接由 PR 新增的 Dockerfile 引起。该 PR 新增了 `Database/percona/8.4.8/24.03-lts-sp3/Dockerfile`，其 `dnf install` 行只安装了基础编译工具链（gcc、cmake、bison、ncurses-devel、openssl-devel、libtirpc-devel、libcurl-devel、shadow），未包含 Percona Server 源码中 LDAP / SASL / Kerberos 认证模块需要的 `openldap-devel`、`cyrus-sasl-devel`、`krb5-devel`。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 第 9 行的 `dnf install -y` 命令中补充三个认证开发库包：`openldap-devel`、`cyrus-sasl-devel`、`krb5-devel`。这与模式10（缺少构建依赖）完全一致，cmake 警告信息中已明确指明了所需包名。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP3 仓库中 `openldap-devel`、`cyrus-sasl-devel`、`krb5-devel` 包的实际可用名称（openEuler 包命名可能与 RHEL/Fedora 略有差异，如 cyrus-sasl 相关包名可能为 `cyrus-sasl-devel` 或 `libsasl2-devel`）。
- 确认 aarch64 架构构建 job 是否因相同原因失败（日志中仅展示了 x86_64 的构建错误，aarch64 未在提供的日志片段中出现）。
