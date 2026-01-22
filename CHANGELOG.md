<!-- @format -->

# Changelog

## 2.2.4 (2026-01-22)

_Commits from: v2.2.3..HEAD_

### 📂 Unscoped changes

#### Bug Fixes

- 🐛 update environment variable assignments and add preinst.resource script

## 2.2.3 (2026-01-22)

_Commits from: v2.2.2..HEAD_

### 📂 Unscoped changes

#### Bug Fixes

- 🐛 revert to postinst
- 🐛 update environment variable paths in presets and substitute scripts

## 2.2.2 (2026-01-22)

_Commits from: v2.2.1..HEAD_

### 📂 Unscoped changes

#### Bug Fixes

- 🐛 ensure proper exit status handling in presets script
- 🐛 move to preinst.resource script for processing presets files

## 2.2.1 (2026-01-22)

_Commits from: v2.2.0..HEAD_

### 📂 Unscoped changes

#### Bug Fixes

- 🐛 correct environment variable references in scripts

## 2.2.0 (2026-01-22)

_Commits from: v2.1.0..HEAD_

### 📂 Unscoped changes

#### Bug Fixes

- 🐛 improve socket handling and clean up code formatting

#### Features

- ✨ improved environment handling and new resource processing

#### Other changes

- 🔧 add guidelines for code changes and commit messages
- ♻️ improve variable extraction logic
- Merge tag 'v2.1.0' into develop
- 🔧 update act feature

## [2.1.0](https://github.com/tomgrv/synology-package-builder/compare/v2.0.0...v2.1.0) (2025-06-12)

### Bug Fixes

- 🐛 update log & config ([4ef9c67](https://github.com/tomgrv/synology-package-builder/commit/4ef9c67da211fd4345a2c50e84c15d82d64080b2))

## [2.0.0](https://github.com/tomgrv/synology-package-builder/compare/v1.5.0...v2.0.0) (2025-06-11)

### ⚠ BREAKING CHANGES

- no more prefix needed for variable substitution

### Features

- ✨ add upgrade daemon ([638615e](https://github.com/tomgrv/synology-package-builder/commit/638615eedef16699d57e705d808f86adecac88b8))
- ✨ add waiting loop ([e921d59](https://github.com/tomgrv/synology-package-builder/commit/e921d598628ec20d8bedfff576a7d8546e29ba4f))
- 💥 ✨ Streamline substitution management ([ec0eece](https://github.com/tomgrv/synology-package-builder/commit/ec0eece775aecf07b30d8dfd8fdbaf5415ca9876))

## [1.5.0](https://github.com/tomgrv/synology-package-builder/compare/v1.4.0...v1.5.0) (2025-06-10)

### Features

- ✨ force package name to CamelCase ([e52f131](https://github.com/tomgrv/synology-package-builder/commit/e52f131ff48c54002ce34d4e6ed3aad02a8de476))

### Bug Fixes

- 🐛 docker path ([3d675bf](https://github.com/tomgrv/synology-package-builder/commit/3d675bfdddfb6d609e5cc19f0ec2c89731e1a6fe))
- 🐛 storage path ([116e82a](https://github.com/tomgrv/synology-package-builder/commit/116e82a09bd49b07230f79423da7ff713bbe6708))
- 🐛 version computation ([f298237](https://github.com/tomgrv/synology-package-builder/commit/f2982375c5727124fc0415e290d4319cfc9f2d65))
- 🐛 version management ([fc05211](https://github.com/tomgrv/synology-package-builder/commit/fc05211c697a722ef66da851c48639b3f9fae460))

## [1.4.0](https://github.com/tomgrv/synology-package-builder/compare/v1.3.0...v1.4.0) (2025-06-09)

## [1.3.0](https://github.com/tomgrv/synology-package-builder/compare/v1.2.0...v1.3.0) (2025-06-08)

### Features

- ✨ improve INFO generation ([ecacdd6](https://github.com/tomgrv/synology-package-builder/commit/ecacdd6e5effb41afdf92312b160836eaf3f899f))

## [1.2.0](https://github.com/tomgrv/synology-package-builder/compare/v1.1.4...v1.2.0) (2025-06-08)

## [1.1.4](https://github.com/tomgrv/synology-package-builder/compare/v1.1.3...v1.1.4) (2025-06-08)

### Bug Fixes

- 🐛 correct path for docker ([f835f76](https://github.com/tomgrv/synology-package-builder/commit/f835f76a7a5a7a75c47788b7c0bc67cd07e2c17d))

## [1.1.3](https://github.com/tomgrv/synology-package-builder/compare/v1.1.2...v1.1.3) (2025-06-07)

## [1.1.2](https://github.com/tomgrv/synology-package-builder/compare/v1.1.1...v1.1.2) (2025-06-07)

### Bug Fixes

- 🐛 config file name ([fcb84bf](https://github.com/tomgrv/synology-package-builder/commit/fcb84bf22128282068827830478f2cd797bf13f8))

## [1.1.0](https://github.com/tomgrv/synology-package-builder/compare/v1.0.3...v1.1.0) (2025-06-07)

### Features

- ✨ add presets management ([2b29bc5](https://github.com/tomgrv/synology-package-builder/commit/2b29bc55c80231bf21fc084da3d6996fbf354a71))

## [0.2.2](https://github.com/tomgrv/synology-package-builder/compare/v0.2.1...v0.2.2) (2024-05-13)

### Bug Fixes

- 🐛 clarify cache path ([b382c53](https://github.com/tomgrv/synology-package-builder/commit/b382c53d85eeb41ece82bf969cb25e5ae1ecdc98))
- 🐛 fix env injection if null ([bf45ade](https://github.com/tomgrv/synology-package-builder/commit/bf45adeaa46d95c19908e85289db910bbef5d0b0))

## [0.2.1](https://github.com/tomgrv/synology-package-builder/compare/v0.2.0...v0.2.1) (2024-05-10)

### Bug Fixes

- 🐛 add cache & fix dockerfile ([68ccf0a](https://github.com/tomgrv/synology-package-builder/commit/68ccf0a700239350de2bda371103c924b34dc39f))

## 0.2.0 (2024-05-09)

### Features

- add build script ([e1fdb2a](https://github.com/tomgrv/synology-package-builder/commit/e1fdb2abd468f6878764c7e68785ff4c9786c25a))

### Bug Fixes

- Fix artifact issue ([b5131af](https://github.com/tomgrv/synology-package-builder/commit/b5131af80743f867a91e92a9469432aed2600f4f))

---

_Generated on 2026-01-22 by [tomgrv/devcontainer-features](https://github.com/tomgrv/devcontainer-features)_
