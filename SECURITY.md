# Security Policy

## Supported versions

Only the latest commit on `main` is supported. Fixes are not backported to
older tags.

## Reporting a vulnerability

Please **do not open a public issue** for security problems.

Report privately through GitHub Security Advisories:
[Report a vulnerability](https://github.com/aimanmalib/codeguard/security/advisories/new)
(repository **Security** tab → **Report a vulnerability**).

Include what you found, how to reproduce it, and the impact you expect. You
should get an acknowledgement within a few days; once a fix is ready it will
land on `main` and the advisory will be published with credit, unless you
prefer to stay anonymous.

## Scope notes

CodeGuard sends the code you review to the LLM endpoint you configure. Treat
that endpoint as a third party: don't review code you aren't allowed to share
with it, and keep API keys in environment variables rather than in config
files you commit.
