# Synology package builder github action

This action builds a synology package

## Inputs

## `dsm`

The version of DSM to target. Default `7.0`.

## `arch`

The architecture of NAS to target. Default `noarch`.

## Example usage

```yml
uses: tomgrv/synology-package-builder@v1
with:
  dsm: 7.0
  arch: avoton
```
