# Homelab

Your home, watched from one small Linux machine (today: homepi). A USB camera you can see from
your phone, motion alarms you switch on when you leave, and one `alarm` command anything else can
use to tell you something. It costs nothing, and only the camera program runs all the time.

## How it works

```
                 on homepi                                        on your phone
 camera ──► camera program ──► motion photo ──► alarm ──► ntfy.sh ──► ntfy app: the alarm
   (USB)    (stream; motion         (only while            (topic)
            only while on)          alarms are on)

 page, live view, switch ◄── Tailscale (your devices only) ◄────────── browser: the page
```

- **Camera:** [mjpg-streamer](https://github.com/350d/mjpg-streamer) at the version tested here
  streams the camera. While motion alarms are on, its motion plugin saves a photo of each movement,
  and that photo goes to your phone at once.
- **Motion alarms are off to start.** Turn them on from the page when you leave and off when you're
  back. Off, nothing looks for motion: no photos, no alarms, less work for the machine.
- **Camera health:** a check every minute, whether alarms are on or off. If the picture stops
  (unplugged, or stuck), you hear once, it restarts by itself, and you hear again when it's back.
- **The page:** the live view, the switch, the camera's state and the last week's motion photos.
  Tapping an alarm opens it.

## Where things live

| What | Where | Who can read it |
|---|---|---|
| **The alarm topic**, the only secret | `/etc/homelab/alarm.conf` on each machine that sends, and your ntfy app | root and the `alarm` group |
| Settings | `/etc/homelab/homelab.conf` | anyone on the machine (no secrets) |
| Motion photos and state | `/var/lib/homelab` | the `homelab` user and root |
| Programs and the page | `/opt/homelab`, `/usr/local/bin/alarm` | anyone (it's this repo) |
| The code | this repo | no secrets in it, ever |

Nothing is in GitHub's secrets, Shipify or Cloudflare.

How things talk:

- **Out:** the machine sends alarms to ntfy.sh over HTTPS. That's the only connection it starts.
- **In:** only through Tailscale, from your own devices, to the page on port 8443. Nothing is open
  to the internet, and the router needs no change.
- **Inside the machine:** the camera (8080) and the page's switch (8081) listen on 127.0.0.1 only,
  and a firewall rule lets only the `homelab` user and root (Tailscale) open them, or the page.
  Other users, such as a Shipify box's agent runs, can't.
- **Whoever knows the topic** can read your alarms and their photos, so it's long and random and
  never appears in a command line, a log, the page or this repo. To replace it:
  `sudo rm /etc/homelab/alarm.conf && sudo ./install`, then subscribe to the new one.

## Set it up

**On your phone, once:** install **ntfy** and **Tailscale**.

**On the machine with the camera:** plug the camera in, put this repo there, and run:

```
sudo ./install
```

One checked step at a time; a step that fails says what to fix:

1. installs what it needs (build tools, curl, jq, nftables);
2. makes your alarm topic and the `alarm` command;
3. makes the `homelab` user: no login, no sudo, only the camera and alarms;
4. builds the camera program;
5. writes the settings, starts the services, and opens the page on Tailscale at
   `https://<machine>.<tailnet>.ts.net:8443`;
6. shows you the topic: in ntfy tap **+**, enter it, tap **Subscribe**, then press Enter;
7. checks it all, and sends a test alarm with the camera's picture.

**Try it:** open the page, tap **Turn on**, wave at the camera: a photo arrives. Unplug it:
"Camera offline" within 3 minutes; plug it back in: "Camera back". Tap **Turn off** when done.

Running it again is safe: it changes only what's different, and keeps your settings, topic,
switch and photos. After a wipe, `sudo ./install --topic` keeps the topic you're subscribed to:
it asks for it (ntfy shows it), so it never shows on a command line.

## Every day

- **Leaving:** open the page, **Turn on**. **Back:** **Turn off**.
- **An alarm:** tap it for the page. The picture refreshes every second; tap the picture for the
  smooth live view, which uses much more data.
- **Someone else** can subscribe to the same topic in their ntfy app.

## Settings

`/etc/homelab/homelab.conf`; after a change, `sudo systemctl restart homelab-camera`.

| Setting | What it does |
|---|---|
| `CAMERA` | which camera (its `/dev/v4l/by-id/…` name stays the same in any USB port) |
| `SIZE`, `FPS` | picture size and frames per second |
| `MOTION` | `--motion 5`: how much must change (%), lower is more sensitive · `--sequence 2`: frames in a row · `--cooldown 120`: seconds between photos · `--zones 3_000010020`: watch only parts (a 3×3 grid, weight 0 to 9 each, left to right, top to bottom) |
| `KEEP_DAYS` | days to keep motion photos |
| `PAGE` | the page an alarm opens |

Use the long option names: the motion plugin doesn't take `-l`.

## Alarms from anything else

`alarm` is one command on the machine, not code to copy or a package to import: the way `logger`
writes to the system log, `alarm` reaches your phone. A script, a timer or another repo's tool
just calls it; where it goes is the machine's setup, in one place.

```
alarm [-p 1-5] [-g tags] [-u link] "title" "message" [photo]

alarm "Backup failed" "The disk is full"
alarm -p 5 -g warning "Water" "The leak sensor is wet" photo.jpg
```

| | |
|---|---|
| `-p` | 1 silent, 2 quiet, 3 normal (default), 4 loud, 5 urgent |
| `-g` | ntfy tags: emoji names, such as `warning` or `rotating_light` |
| `-u` | a link the phone opens when you tap the alarm |
| exit 0 | delivered to the alarm server |
| exit 1 | not delivered: the reason is on stderr (no internet, the daily limit, no topic) |
| exit 2 | wrong arguments: the usage is on stderr |

- **Who may send:** root and the `alarm` group (`sudo usermod -aG alarm <user>`).
- **Another machine:** put this repo there and run `sudo ./install alarm --topic` (it asks for the topic).
  It installs only the command; the same topic is the same place on your phone.
- **A caller handles failure itself:** `alarm … || echo "alarm not sent" >&2`. Don't hide it.
- **Somewhere that can't run the command** sends the same fields to the topic over HTTPS (ntfy's
  API: `Title`, `Priority`, `Tags`, `Click`, and the message as the body). There the topic is a
  secret like any key.

## With Shipify

Homelab shares homepi with a Shipify box. They don't touch:

- **Shipify talks; homelab alarms.** Shipify's work and replies stay in Shipify's chats, and
  nothing of Shipify calls `alarm`. Shipify can change this repo by a PR (`homelab: …`), tested by
  its CI; you apply a merged change here with `sudo ./install`. Nothing deploys from GitHub.
- **Its own user, folders and services:** `homelab`; `/opt/homelab`, `/etc/homelab`,
  `/var/lib/homelab`; `homelab-*`. Each service is sandboxed: no view of `/home` or `/srv`, and
  it writes only to its own folder.

## Update, or remove

- **Update:** get the new files here (`git pull`, or copy), then `sudo ./install`.
- **Remove:** `sudo ./install remove` takes away the services, page, programs, settings, topic,
  photos, user and group. The build packages stay.

## When something's wrong

| You see | Do |
|---|---|
| No alarms at all | Subscribed to the topic in ntfy? Muted? Motion alarms on? `sudo ./install` again sends a test alarm |
| "Camera offline" and it stays | Plug the camera in, or try another USB port. `journalctl -u homelab-camera -n 20` |
| Too many motion alarms | Raise `--motion` or `--cooldown`, or use `--zones` to skip a busy part |
| Missed motion | Lower `--motion` or `--sequence` |
| The page doesn't open | Tailscale on? On the machine, `tailscale serve status` lists port 8443 |
| The switch says it didn't switch | `journalctl -u 'homelab-api*' -n 20` |
| The page says the last alarm didn't reach your phone | ntfy.sh allows 250 alarms a day; the next motion photo tries again |

Logs: `journalctl -u 'homelab-*'`. Status: `systemctl list-units 'homelab-*'`.

## Limits

- **ntfy.sh, free:** 250 alarms a day, photos up to 15 MB, kept there 3 hours (then only on your
  phone and here). For more, or for photos that never leave home, run your own ntfy server and
  give `sudo ./install --topic` its address: `https://your.server/topic`.
- **Pixel motion,** not people: light changes and pets can trip it. `--zones` and `--motion` tune it.

## What's where

| | |
|---|---|
| `install` | the one command: set up, `alarm`, `remove` |
| `bin/alarm` | the alarm command |
| `lib/camera-run` | starts the camera program (motion only while alarms are on) |
| `lib/motion-send` | sends a new motion photo as an alarm |
| `lib/check` | the minute check: camera health, the page's status, old photos |
| `lib/motion-switch`, `lib/api` | the switch, and the page's way to it |
| `lib/firewall` | the rule that keeps other users here out |
| `systemd/` | the services: `homelab-camera`, `homelab-motion` (path), `homelab-check` (timer), `homelab-api` (socket), `homelab-firewall` |
| `www/index.html` | the page |
| `test/run` | the tests, against a stand-in for ntfy and the camera |
