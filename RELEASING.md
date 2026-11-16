# Releasing

The action runs a prebuilt image from `ghcr.io/peterus/platformio_dependabot`, and `action.yml`
points to the image of exactly one release. Every release therefore needs two steps:

1. **Bump the image tag** in `action.yml` to the new version and merge that to `main`:

   ```yaml
   runs:
     using: 'docker'
     image: 'docker://ghcr.io/peterus/platformio_dependabot:vX.Y.Z'
   ```

2. **Publish a GitHub release** `vX.Y.Z` from `main`.

The [release workflow](.github/workflows/release.yml) then

* checks that `action.yml` at the tag references `vX.Y.Z` (fails otherwise),
* builds the `Dockerfile` and pushes `ghcr.io/peterus/platformio_dependabot:vX.Y.Z`,
* and only then moves the major tag (`v1`) to the release.

If the check fails, delete the release and its tag, fix `action.yml` on `main` and release again.
Until the image is pushed (about a minute), `@vX.Y.Z` cannot be used yet; `@v1` is not affected.
