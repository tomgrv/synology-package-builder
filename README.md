<!-- @format -->

[![](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/PeterSuh-Q3)
[![GitHub release](https://img.shields.io/github/release/PeterSuh-Q3/synology-package-builder?include_prereleases=&sort=semver&color=blue)](https://github.com/tomgrv/synology-package-builder/releases/)
[![License](https://img.shields.io/badge/License-MIT-blue)](#license)
[![issues - synology-package-builder](https://img.shields.io/github/issues/tomgrv/synology-package-builder)](https://github.com/tomgrv/synology-package-builder/issues)

# < NOTE >

The Change Panel Size package repo has been moved to the following link:

https://github.com/PeterSuh-Q3/ChangePanelSize/releases

The Syno Smart Info package repo has been moved to the following link:

https://github.com/PeterSuh-Q3/SynoSmartInfo/releases


# < Caution >

Changepanelsize, Synosmartinfo synology user must be granted the authority to process with sudoers.

Check if the file already exists with the command below, and if not,

sudores processing as below is absolutely necessary.

If sudores does not exist, panel size change will not be processed due to insufficient authority.


```
sudo -i
ll /etc/sudoers.d/Changepanelsize
ll /etc/sudoers.d/Synosmartinfo
```

```
sudo -i
echo "changepanelsize ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/Changepanelsize
echo "synosmartinfo ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/Synosmartinfo
chmod 0440 /etc/sudoers.d/Changepanelsize
chmod 0440 /etc/sudoers.d/Synosmartinfo
```

# Synology package builder github action

This action generates a synology package according to [Synology Developper Guide](https://help.synology.com/developer-guide/getting_started/first_package.html)

## Inputs

### `dsm`

The version of DSM to target. Defaults to `7.0`.

### `arch`

The architecture to target. Defaults to `noarch`.

### `projects`

The source of projects. Defaults to `./src`

> Must be under the `alias:./path/to/package` form if several sources with the same final package folder.
>
> ```yml
>  ...
>  projects: |-
>      front-pack:./src/front/package
>      back-pack:./src/back/package
> ```

### `output`

The output directory for the generated packages. Defaults to `./dist`

## Example usage

### Step

Default usage with one project in src folder:

```yml
- uses: tomgrv/synology-package-builder@v1
  with:
      dsm: 7.0
      arch: avoton
```

Custom usage with multiple project in arbitrary folders:

```yml
- uses: tomgrv/synology-package-builder@v1
  with:
      dsm: 7.0
      arch: avoton
      projects: |-
          ./src/web_package_example
          ./src/ExamplePackage
      output: ./dist
```

### Artifacts

To retrieve packages:

```yml
- uses: actions/upload-artifact@v4
  with:
      name: packages
      path: ./dist/*.spk
```

### Matrix

To build for multiple DSM versions and architectures, you can use a matrix strategy:

```yml
jobs:
    build:
        runs-on: ubuntu-latest
        strategy:
            matrix:
                dsm: [7.0, 7.1]
                arch: [noarch, avoton, x86_64]
        steps:
            - uses: actions/checkout@v3
            - uses: tomgrv/synology-package-builder@v1
              with:
                  dsm: ${{ matrix.dsm }}
                  arch: ${{ matrix.arch }}
```

## Project Structure

See [Project Structure](./doc/structure.md) for details on how to structure your Synology package project.

## Elevated Privileges

This action provides a way to install packages requiring elevated privileges.

See [Elevated Privileges](./doc/elevated.md) for details on how to use it.

## Exemples

See [tests results](https://github.com/tomgrv/synology-package-builder/actions/workflows/test.yaml) with [SynologyOpenSource/ExamplePackages](https://github.com/SynologyOpenSource/ExamplePackages)

See https://github.com/tomgrv/synology-github-runner

## License

This repository is licensed under the [MIT License](LICENSE).

This work is not affiliated with Synology Inc. in any way. It is an independent project that aims to facilitate the development of Synology packages using GitHub Actions. It is not an official Synology product and does not have any official support from Synology Inc. Use at your own risk.
