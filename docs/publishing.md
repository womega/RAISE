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

For the first upload, configure a pending publisher in PyPI account settings under
Publishing. A pending publisher creates the project on first use and then becomes
an ordinary project publisher. It does not reserve the project name. If the pending
entry above is already present, do not create a duplicate or remove it.

## Configure the GitHub environment

1. Open https://github.com/womega/RAISE/settings/environments.
2. Create or open the environment named `pypi`.
3. Under deployment branches and tags, choose **Selected branches and tags** and add
   a **Tag** rule matching `v*`. A branch-only `main` rule does not allow release tags.
4. Optionally require approval from `womega`. If you are the only approver and also
   create releases, leave **Prevent self-review** disabled so you can approve them.
5. Save the environment settings. No environment secrets are required for OIDC.

## First upload: 0.1.1

An existing GitHub release/tag `v0.1.0` points to the older code before the CI fixes.
Leave it intact. The release prepared here is `0.1.1`, which can be the first
version published on PyPI; publishing `0.1.0` there first is not required.

1. Merge the release-preparation PR into `main` and wait for its CI to pass.
2. Confirm `src/raise_xai/__about__.py` contains `__version__ = "0.1.1"`,
   `CITATION.cff` says `version: 0.1.1`, and the changelog has the corresponding entry.
3. Optional preflight: in Actions, select **Publish to PyPI**, choose **Run workflow**,
   and select `main`. The build should pass and the publish job should be skipped.
   This checks the distribution build, not PyPI authentication.
4. Open https://github.com/womega/RAISE/releases/new.
5. Choose a **new tag** `v0.1.1`, with the target set to the updated `main` branch.
   Do not select the existing `v0.1.0` tag.
6. Use the title **RAISE v0.1.1**, describe the package and CI fixes from the changelog,
   and click **Publish release** when ready. Saving a draft does not publish to PyPI.
7. Open the new release-triggered **Publish to PyPI** run. The `build` job runs
   checks, builds the sdist and wheel, tests the installed wheel, and uploads artifacts.
8. If configured, approve the `pypi` environment deployment under **Review deployments**.
9. The `publish` job downloads those artifacts and uploads them to production PyPI.
   Wait for that job to succeed before announcing pip installation availability.

Do not rerun the old `v0.1.0` workflow to pick up fixes from `main`: GitHub reruns
use the original event's commit and ref. Merely editing old release notes or pushing
a tag does not satisfy this workflow's `release: published` trigger.

## Verify the published package

Open https://pypi.org/project/raise-xai/0.1.1/ and confirm both distribution files
are present. The pending publisher should now appear under the project's active
publishing configuration.

Use a new environment outside a source checkout (macOS/Linux):

```bash
python3 -m venv /tmp/raise-pypi-check
source /tmp/raise-pypi-check/bin/activate
python -m pip install --upgrade pip
python -m pip install --index-url https://pypi.org/simple "raise-xai==0.1.1"
python -m pip check
python -c "from importlib.metadata import version; from raise_xai import RAISEExplainer; print(version('raise-xai'))"
```

Use a fresh directory name if that environment already exists. On Windows, use
`py -m venv .venv` and `.venv\Scripts\Activate.ps1` in PowerShell instead.
The version command should print `0.1.1`. Then run the README's tokenizer-aligned
quickstart to verify fitting and explanation retrieval.

Users can subsequently install with `python -m pip install raise-xai` or upgrade
with `python -m pip install --upgrade raise-xai`. Python imports use `raise_xai`.

## Later releases

Update `src/raise_xai/__about__.py`, `CITATION.cff`, and `CHANGELOG.md` in a PR.
After merging and passing CI, publish a new GitHub release with a matching tag
(for example, package version `0.1.2` and tag `v0.1.2`). Keep the same publisher
configuration. Never move an existing release tag or attempt to replace uploaded files.

The README is embedded in each built distribution. Changes on GitHub do not change
the long description of an already-uploaded release; include them in a new version.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `publish` skipped | Expected for PRs and manual dispatch. Use a newly published GitHub release to upload. |
| Waiting for approval | Approve the `pypi` deployment if required reviewers are enabled. |
| Environment rejects the ref | Ensure the environment allows **Tag** pattern `v*`, not only branch `main`. |
| OIDC publisher mismatch | Check owner, repository, workflow filename, and environment against the table above. Keep `id-token: write` on the publish job. |
| Existing file/version error | Inspect PyPI before retrying. Do not delete published files to reuse their names. For an incomplete or incorrect upload, prepare a new version after diagnosing the failure. |
| Package not found by pip | Confirm the publish job succeeded, the PyPI project exists, Python is at least 3.10, and pip is using production PyPI. |

If authentication fails before any files upload, correct the publisher/environment
configuration and rerun the failed publish job for the new release. If source or
workflow changes are needed, prepare a new version/tag rather than expecting a rerun
to use updated `main` code.

## References

- [PyPI: creating a project with a Trusted Publisher](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
- [PyPI: publishing with a Trusted Publisher](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
- [GitHub: managing environments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
- [GitHub: rerunning workflows and jobs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs)
