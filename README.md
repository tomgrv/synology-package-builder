# Synology package builder github action

This action generates a synology package according to [Synology Developper Guide](https://help.synology.com/developer-guide/getting_started/first_package.html)

## Inputs

### `dsm`

The version of DSM to target. Defaults to `7.0`.

### `arch`

The architecture to target. Defaults to `noarch`.

### `projects`

The source of projects. Defaults to `./src`

>
> Must be under the `alias:./path/to/package` form if several sources with the same final package folder.
>
> ```yml
>  ...
>  projects: |-
>      front-pack:./src/front/package
>      back-pack:./src/back/package
> ```
>

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
```

### Artifacts

To retrieve packages:

```yml
- uses: actions/upload-artifact@v3
  with:
    name: packages
    path: ./toolkit/result_spk/**/*.spk
```
