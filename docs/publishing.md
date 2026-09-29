# Publishing raise-xai to PyPI

## Publisher identity

The repository uses GitHub Actions Trusted Publishing (OIDC). No PyPI API token,
username, password, or repository secret is needed by the publishing job.

| PyPI setting | Required value |
| --- | --- |
| Project name | `raise-xai` |
| GitHub owner | `womega` |
| Repository | `RAISE` |
| Workflow filename | `release.yml` |
| Environment name | `pypi` |

The workflow is `.github/workflows/release.yml`; the PyPI form takes only its filename.
The workflow's display name is **Publish to PyPI**. The publish job requests
`id-token: write` and uses `pypa/gh-action-pypi-publish@release/v1`.

For first-time project setup only, configure the matching trusted publisher in PyPI.
Once the project exists, keep the active publisher configuration rather than creating
a duplicate pending publisher.

## Release-version guard

On release-triggered runs, the build job first executes
`scripts/check_release_version.py`. The GitHub release tag is passed through an
environment variable rather than interpolated into shell source. The guard requires
an exact `v<package-version>` match with the single literal `__version__` assignment
in `src/raise_xai/__about__.py`.

For example, a package version of `0.1.2` requires the release tag `v0.1.2`. A tag
such as `v0.1.3`, `0.1.2`, or a source file with multiple/non-literal `__version__`
assignments fails the build before checks, distribution building, artifact upload,
or PyPI publishing. Pull-request and manual-dispatch runs skip this release-only
check, while the normal test suite exercises the guard itself.

## Configure the GitHub environment

1. Open https://github.com/womega/RAISE/settings/environments.
2. Create or open the environment named `pypi`.
3. Under deployment branches and tags, choose **Selected branches and tags** and add
   a **Tag** rule matching `v*`. A branch-only `main` rule does not allow release tags.
4. Optionally require approval from `womega`. If you are the only approver and also
   create releases, leave **Prevent self-review** disabled so you can approve them.
5. Save the environment settings. No environment secrets are required for OIDC.

## Release process

1. Choose the next version before creating a tag. Update
   `src/raise_xai/__about__.py`, `CITATION.cff`, and `CHANGELOG.md` in the same PR.
2. Merge the release-preparation PR into `main` and wait for CI to pass.
3. Confirm the version values and changelog entry on the merged `main` branch.
4. Optional preflight: in Actions, select **Publish to PyPI**, choose **Run workflow**,
   and select `main`. The build should pass and the publish job should be skipped.
   This validates the package build but does not exercise release-tag validation or
   PyPI authentication.
5. Create a **new** GitHub release tag from the updated `main` commit using the exact
   form `v<package-version>` (for example, package `0.1.2` -> tag `v0.1.2`).
6. Publish the GitHub release. Saving a draft does not publish to PyPI.
7. Open the release-triggered **Publish to PyPI** run. The `build` job verifies the
   tag/package match, runs checks, builds the sdist and wheel, tests the installed
   wheel, and uploads the distribution artifact.
8. If configured, approve the `pypi` environment deployment under
   **Review deployments**.
9. The `publish` job downloads the exact artifact produced by the successful build
   job and uploads it to production PyPI through OIDC.
10. Wait for the publish job to succeed and verify the new release on PyPI before
    announcing installation availability.

Never move or reuse an existing release tag to publish different source. GitHub reruns
use the original event's commit and ref, and PyPI distribution filenames are immutable.
If source or workflow changes are needed after a release attempt, diagnose the issue
and prepare an appropriate new release rather than assuming a rerun will use current
`main`.

## Verify the published package

Confirm the expected version page on PyPI contains both the wheel and source
distribution. Then verify from a clean environment outside the source checkout.
For example, replace `0.1.2` below with the version just published:

```bash
python3 -m venv /tmp/raise-pypi-check
source /tmp/raise-pypi-check/bin/activate
python -m pip install --upgrade pip
python -m pip install --index-url https://pypi.org/simple "raise-xai==0.1.2"
python -m pip check
python -c "from importlib.metadata import version; from raise_xai import RAISEExplainer; print(version('raise-xai'))"
```

Use a fresh directory name if that environment already exists. On Windows, use
`py -m venv .venv` and `.venv\Scripts\Activate.ps1` in PowerShell instead. The
version command must print the version that was just released. Then run the README's
tokenizer-aligned quickstart to verify fitting and explanation retrieval.

Users can install with `python -m pip install raise-xai` or upgrade with
`python -m pip install --upgrade raise-xai`. Python imports use `raise_xai`.

The README is embedded in each built distribution. Changes on GitHub do not change
the long description of an already-uploaded release; include them in a new version.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Release-version guard fails | Confirm the release tag is exactly `v` plus the value in `src/raise_xai/__about__.py` and that the source contains one literal `__version__` assignment. Prepare the version bump before creating the release tag. |
| `publish` skipped | Expected for PRs and manual dispatch. Use a newly published GitHub release to upload. |
| Waiting for approval | Approve the `pypi` deployment if required reviewers are enabled. |
| Environment rejects the ref | Ensure the environment allows **Tag** pattern `v*`, not only branch `main`. |
| OIDC publisher mismatch | Check owner, repository, workflow filename, and environment against the table above. Keep `id-token: write` on the publish job. |
| Existing file/version error | Inspect PyPI before retrying. Do not delete published files to reuse their names. Diagnose the failure and prepare an appropriate new release if source must change. |
| Package not found by pip | Confirm the publish job succeeded, the PyPI project exists, Python is at least 3.10, and pip is using production PyPI. |

If authentication fails before any files upload and the release source itself is
correct, fix the publisher/environment configuration and rerun the failed publish
job. If source, version, tag, or workflow changes are required, prepare a new release
rather than expecting a rerun to use updated `main`.

## References

- [PyPI: creating a project with a Trusted Publisher](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
- [PyPI: publishing with a Trusted Publisher](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
- [GitHub: managing environments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
- [GitHub: rerunning workflows and jobs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs)
