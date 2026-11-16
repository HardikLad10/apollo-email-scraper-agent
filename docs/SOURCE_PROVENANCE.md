# Source provenance

- Upstream: https://github.com/pratyushagarwal22/job-hunt-tools
- Imported branch: `master`
- Imported commit: `ffe7aee7a57aa9030d886ebb00089579fe867041`
- Acquisition: GitHub's **Download ZIP** in the browser. The archive comment contains
  the full commit above.
- Archive: `job-hunt-tools-master.zip`
- SHA-256: `33cca9e66331b47cb303394b883dcb78e3431a72419025e822fa0d89757a8942`
- Session date: November 13, 2026, America/Chicago.
- Imported files: 79; contents were checked byte-for-byte against the archive.
- Import layout: stripped the archive's enclosing `job-hunt-tools-master/` directory
  and placed its contents directly in this project folder.

## Git status and remaining setup

This is a downloaded source snapshot. It has no upstream Git objects/history and is
not a GitHub fork. No new Git repository, branch, commit, push, or remote was created.
The enclosing `job-search` directory is already a different Git repository.

Terminal access to `github.com` failed DNS resolution in this environment. GitHub CLI
reported an invalid login for `HardikLad10`. The browser could read and download the
public source while signed out. These limitations did not prevent the source review.

To finish the fork, restore GitHub authentication and fork upstream under the intended
account, then clone with full history and retain an `upstream` remote pointing to the
friend's repository. Preserve these local documents when replacing the snapshot.
Do not invent ancestry or push this folder through the enclosing repository.

## Local additions

`scope.md`, `AGENTS.md`, `CLAUDE.md`, `CHANGELOG.md`, this provenance document, and
`docs/CODEBASE_REVIEW.md` were added for Hardik's pilot. None came from upstream.

No real API keys, Google service-account files, contact lists, or private candidate
files were imported from the public archive. No `LICENSE` file is present in this
snapshot. No upstream source, settings, tests, examples, or workflow was edited.


## Git history restoration and new origin — November 15, 2026

The earlier acquisition notes describe the initial import. GitHub authentication is
now working. Cloned the original upstream history without checking out over local
files, verified the imported commit, and attached independent Git metadata to this
project. The working tree is based on ffe7aee7a57aa9030d886ebb00089579fe867041;
newer upstream work was not silently merged. The surrounding repository was untouched.

The user's requested destination is the private repository
https://github.com/HardikLad10/apollo-email-scraper-agent with origin there and upstream
at https://github.com/pratyushagarwal22/job-hunt-tools. This is an independent repository
with retained ancestry, not a GitHub fork-network claim. Initial local additions and
the pilot implementation are committed on main. The inherited scanner YAML is moved
to .github/disabled-workflows/scan.yaml so it cannot start its inherited cron.
Secrets, candidate profile, contact records/exports and the virtual environment remain
ignored and are not publication inputs. Initial baseline review findings remain
historical; current behavior is recorded in scope, guide and appended CHANGELOG.
