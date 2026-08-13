# Privacy and sharing

Glasshouse reads local Claude Code, Codex, and Cursor activity. Processing is
local and Glasshouse does not currently collect telemetry.

- Raw transcripts are not embedded in reports.
- Common credentials, emails, IP addresses, and home paths are scrubbed from
  report text.
- Optional pull-request enrichment uses the user's existing authenticated `gh`
  session and can be disabled with `--no-gh`.
- Generated HTML includes no analytics script or remotely loaded asset.

Reports may contain selected prompt text. Ask the user to review the HTML before
sharing it publicly, including when the command reports a scrub count of zero.
