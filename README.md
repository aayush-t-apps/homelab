# Home

A camera that watches home and tells your phone when something moves, plus one `alarm` command
that anything else can use to tell you something. It runs on one Linux machine with a USB camera
(today: homepi), costs nothing, and needs nothing running but the camera program.

```
 camera: motion seen    ──┐
 camera: offline, back  ──┤   alarm "title" "message" [photo]   ──►  ntfy.sh topic  ──►  ntfy app
 any script or machine  ──┘          (one web request)                                   on your phone
```

- **Motion:** the camera program ([mjpg-streamer](https://github.com/350d/mjpg-streamer), at the
  version tested here) saves a photo when something moves. That photo goes to your phone at once.
- **Camera health:** a check every minute. If the picture stops (unplugged, or stuck), you hear
  once, it restarts by itself, and you hear again when it's back.
- **The page:** live view, the camera's state and the last week's motion photos, on your own
  devices only (through Tailscale). Tapping an alarm opens it.
- **Alarms** are one-way messages to your phone, through a private topic on
  [ntfy.sh](https://ntfy.sh). Whoever knows the topic can read them, so it's long and random.

## Set it up

**On your phone, once:** install **ntfy** (Play Store or App Store), and **Tailscale** for the page.

**On the machine with the camera:** plug the camera in, copy this repo onto it, and run:

```
sudo ./install
```

It goes one checked step at a time, and stops with what to fix if a step fails:

1. installs what it needs (build tools, curl, jq, nftables);
2. makes your alarm topic and the `alarm` command;
3. makes the `homecam` user: no login, no sudo, only the camera and alarms;
4. builds the camera program;
5. writes the settings (`/etc/home/home.conf`), starts the services, and opens the page on
   Tailscale at `https://<machine>.<tailnet>.ts.net:8443`;
6. shows you the topic: in ntfy tap **+**, enter it, tap **Subscribe**, then press Enter;
7. checks it all, and sends a test alarm with the camera's picture.

**Test it:** wave at the camera, and a photo alarm arrives. Unplug it: "Camera offline" arrives
within 3 minutes. Plug it back in: "Camera back".

Running it again is safe: it changes only what's different, and keeps your settings, topic and
photos. After a wipe, `sudo ./install --topic <your topic>` (the ntfy app shows it) keeps the
topic you're subscribed to.

## Every day

- **Tap an alarm** to open the page (Tailscale on). The picture refreshes every second; tap it for
  the smooth live view, which uses much more data.
- **At home,** mute the topic in ntfy so motion doesn't ring.
- **Someone else** can subscribe to the same topic in their ntfy app.

## Settings

`/etc/home/home.conf`; after a change, `sudo systemctl restart home-camera`.

| Setting | What it does |
|---|---|
| `CAMERA` | which camera (its `/dev/v4l/by-id/…` name stays the same in any USB port) |
| `SIZE`, `FPS` | picture size and frames per second |
| `MOTION` | `--motion 5`: how much must change (%), lower is more sensitive · `--sequence 2`: frames in a row · `--cooldown 120`: seconds between motion photos · `--zones 3_000010020`: watch only parts (a 3×3 grid, weight 0 to 9 each, left to right, top to bottom) |
| `KEEP_DAYS` | days to keep motion photos |
| `PAGE` | the page an alarm opens |

Use the long option names: the motion plugin doesn't take `-l`.

## Alarms from anything else

```
alarm "Backup failed" "The disk is full"
alarm -p 5 -g warning "Water" "The leak sensor is wet" photo.jpg
```

`-p` is 1 (silent) to 5 (urgent), `-g` ntfy tags (emoji names), `-u` a link to open. Root and
the `alarm` group may send (`sudo usermod -aG alarm <user>`). On another machine,
`sudo ./install alarm --topic <your topic>` installs only the command.

## How it stays separate

It shares homepi with a Shipify box, and the two don't touch:

- **Shipify talks; home alarms.** Shipify's work and replies stay in Shipify's chats, and nothing
  of Shipify calls `alarm`. Shipify can change this repo by a PR (`home: …`); you apply it here.
- **Its own user, folders and services:** `homecam`; `/opt/home`, `/etc/home`, `/var/lib/home`;
  `home-*`. The services are sandboxed: no view of `/home` or `/srv`, writes only to their folder.
- **The camera and the page are closed to other users here,** agent runs included: a firewall
  rule lets only `homecam` and root (Tailscale) open ports 8080 and 8443 on this machine. The topic
  is readable only by root and the `alarm` group, and never appears on a command line.

## Update, or remove

- **Update:** get the new files here (`git pull`, or copy), then `sudo ./install`.
- **Remove:** `sudo ./install remove` takes away the services, page, programs, settings, topic,
  photos, user and group. The build packages stay.

## When something's wrong

| You see | Do |
|---|---|
| No alarms at all | Subscribed to the right topic in ntfy? Is it muted? `sudo ./install` again sends a test alarm |
| "Camera offline" and it stays | Plug the camera in, or try another USB port. `journalctl -u home-camera -n 20` |
| Too many motion alarms | Raise `--motion`, raise `--cooldown`, or use `--zones` to skip a busy part |
| Missed motion | Lower `--motion` or `--sequence` |
| The page doesn't open | Tailscale on? `tailscale serve status` on the machine should list port 8443 |
| The page says the last alarm didn't reach your phone | ntfy.sh allows 250 alarms a day; the next motion photo tries again |

Logs: `journalctl -u 'home-*'`. Status: `systemctl list-units 'home-*'`.

## Limits and privacy

- **ntfy.sh, free:** 250 alarms a day, photos up to 15 MB, kept there 3 hours (then only on your
  phone and here, `KEEP_DAYS`). For more, or for photos that never leave home, run your own ntfy
  server and `sudo ./install --topic https://your.server/topic`.
- **The page** is only on your Tailscale devices; nothing is open to the internet.

## What's where

| | |
|---|---|
| `install` | the one command |
| `bin/alarm` | the alarm command |
| `lib/camera-run`, `lib/motion-send`, `lib/check`, `lib/firewall` | what the services run |
| `systemd/` | the services: `home-camera`, `home-motion` (path), `home-check` (timer), `home-firewall` |
| `www/index.html` | the page |
| `test/run` | the tests, against a stand-in for ntfy and the camera |
