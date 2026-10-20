# Homelab: agent guide

The home camera (off, live view only, or on while you're away: live view and motion photos), its
page, and the `alarm` command (README.md). Your work ends
at a PR; the owner's merge is the approval, and each machine installs `main` by itself the next
day (`lib/update`). So `main` must always install cleanly: CI runs the checks below on every PR.

## Rules

- **Never read or print the alarm topic** (`/etc/homelab/alarm.conf`, `ALARM_URL`): whoever knows
  it reads the owner's alarms and photos. Tests use a stand-in server.
- **Shipify never calls `alarm`,** and homelab never posts to Shipify: Shipify talks, homelab alarms.
- **Keep it small:** bash, systemd units, one static page, coreutils, curl and jq. Nothing new that
  runs all the time, and no new service or dependency, without the owner's yes.
- **Every failure says what to do,** in plain words, and nothing fails silently: the page shows
  the last alarm that didn't send.
- **`install` stays idempotent:** a second run changes nothing, and keeps settings, topic, switch
  and photos.
- **Only the homelab user and root reach the camera, the switch and the page** on the machine
  (`lib/firewall`). A new local port goes into that rule.
- **The camera program is pinned** (`MJPG_COMMIT` in `install`). Changing it is its own PR, tested
  on the camera. Its motion plugin takes long option names only (`--motion`, not `-l`).

## Check before the PR

```
shellcheck -x install bin/alarm lib/* test/run
test/run
```

A behaviour change adds a test to `test/run` that fails without it. Update README.md in the same PR.
