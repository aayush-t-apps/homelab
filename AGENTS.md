# Home: agent guide

The home camera and the `alarm` command (README.md). The owner applies every change on the machine
with `sudo ./install`: your work ends at a PR.

## Rules

- **Never read or print the alarm topic** (`/etc/home/alarm.conf`, `ALARM_URL`): whoever knows it
  reads the owner's alarms. Tests use a stand-in server.
- **Shipify never calls `alarm`,** and home never posts to Shipify: Shipify talks, home alarms.
- **Keep it small:** bash, systemd units, one static page, coreutils, curl and jq. No new
  long-running process, service or dependency without the owner's yes.
- **Every failure says what to do,** in plain words, and nothing fails silently: the page shows
  the last alarm that didn't send.
- **`install` stays idempotent:** a second run changes nothing, and keeps settings, topic and photos.
- **The camera program is pinned** (`MJPG_COMMIT` in `install`). Changing it is its own PR, tested
  on the camera. Its motion plugin takes long option names only (`--motion`, not `-l`).

## Check before the PR

```
shellcheck -x install bin/alarm lib/* test/run
test/run
```

A behaviour change adds a test to `test/run` that fails without it. Update README.md in the same PR.
