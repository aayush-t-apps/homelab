# Homelab

Your home, watched from one small Linux machine (today: homepi). A USB camera you turn on when you
leave: you see it from your phone, and each movement sends you a photo. And one `alarm` command
anything else can use to tell you something. It costs nothing, and while the camera is off, nothing
runs for it.

## How it works

```
                 on homepi, while the camera is on                on your phone
 camera ──► camera program ──► motion photo ──► alarm ──► ntfy.sh ──► ntfy app: the alarm
   (USB)    (live stream and                               (topic)
             motion detection)

 page: live view, switch ◄── Tailscale (your devices only) ◄────────── browser: the page
```

- **The camera is off to start,** and whenever you're home: it isn't used at all, nothing is seen
  or saved, and nothing runs for it. Turn it on from the page when you leave, off when you're back.
  The machine remembers it, through restarts and updates.
- **On,** [mjpg-streamer](https://github.com/350d/mjpg-streamer) (at the version tested here)
  streams the camera at 1280x720, and its motion plugin saves a photo when something moves.
  - **Your phone** gets an alarm about a second after you walk into view, with a frame taken half a
    second after the movement began, so whoever moved is in it.
  - **The page** then gets three more frames, half a second apart, so you see what happened; and
    while something keeps moving, a photo every 10 seconds.
  - **Alarms are paced:** at most one every 30 seconds, saying how many photos came since the last,
    and at most 200 a day. ntfy.sh's free limit is 250 a day: past 200 you get one notice, the page
    still gets every photo, and alarms return at midnight.
  - **Light isn't someone:** the first 10 seconds after the camera starts (its light settling)
    and a change of almost the whole picture at once (a lamp switched on) are ignored.
- **Camera health,** while it's on: a check every minute. If the picture stops (unplugged, or
  stuck), you hear once, it restarts by itself, and you hear again when it's back.
- **The page:** the live view, the switch, the camera's state and the last week's motion photos.
  Tapping an alarm opens it.

## Where things live

| What | Where | Who can read it |
|---|---|---|
| **The alarm topic**, the only secret | `/etc/homelab/alarm.conf` on each machine that sends, and your ntfy app | root and the `alarm` group |
| Settings | `/etc/homelab/homelab.conf` (this machine's), `/opt/homelab/defaults.conf` (homelab's) | anyone on the machine (no secrets) |
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
  `sudo rm /etc/homelab/alarm.conf && sudo /opt/homelab/src/install`, then subscribe to the new one.

## Set it up

**On your phone, once:** install **ntfy** and **Tailscale**.

**On the machine with the camera:** plug the camera in, and run:

```
sudo git clone https://github.com/aayush-t-apps/homelab /opt/homelab/src
sudo /opt/homelab/src/install
```

(No git? `sudo apt install -y git` first. For only the alarm command, the second line is
`sudo /opt/homelab/src/install alarm --topic`.)

One checked step at a time; a step that fails says what to fix:

1. installs what it needs (build tools, curl, jq, nftables);
2. makes your alarm topic and the `alarm` command;
3. makes the `homelab` user: no login, no sudo, only the camera and alarms;
4. builds the camera program;
5. writes the settings, starts the services, and opens the page on Tailscale at
   `https://<machine>.<tailnet>.ts.net:8443`;
6. shows you the topic: in ntfy tap **+**, enter it, tap **Subscribe**, then press Enter;
7. checks it all, and sends a test alarm with the camera's picture;
8. sets up the daily update (below).

**Try it:** open the page, tap **Turn on**, wave at the camera: a photo arrives. Unplug it:
"Camera offline" within 3 minutes; plug it back in: "Camera back". Tap **Turn off** when done.

Running it again is safe: it changes only what's different, and keeps your settings, topic,
switch and photos. After a wipe, `sudo /opt/homelab/src/install --topic` keeps the topic you're subscribed to:
it asks for it (ntfy shows it), so it never shows on a command line.

## Every day

- **Leaving:** open the page, **Turn on**. **Back:** **Turn off**.
- **An alarm:** tap it for the page. The live view is smooth (about 7 Mbit/s); tap the picture for
  one picture a second, which saves mobile data (it starts that way when your phone saves data).
- **Someone else** can subscribe to the same topic in their ntfy app.

## Settings

Two files, read in this order:

- **`/opt/homelab/defaults.conf`:** homelab's defaults, from this repo. Don't edit it: an update
  replaces it, and can improve it.
- **`/etc/homelab/homelab.conf`:** this machine's camera and page, and anything you change. Copy a
  line from the defaults here and change it: yours wins, through every update. After a change,
  `sudo systemctl restart homelab-camera`.

| Setting | What it does | Default |
|---|---|---|
| `CAMERA` | which camera (its `/dev/v4l/by-id/…` name stays the same in any USB port) | found by install |
| `PAGE` | the page an alarm opens | found by install |
| `SIZE`, `FPS` | picture size, frames per second | `1280x720`, `15` |
| `MOTION` | `--motion`: how much must change, in % (lower is more sensitive) · `--overload`: more than this changing at once is the light, ignored · `--sequence`: frames in a row · `--cooldown`: seconds between photos · `--zones 3_000010020`: watch only parts (a 3×3 grid, weight 0 to 9 each, left to right, top to bottom) | `--motion 5 --overload 90 --sequence 2 --cooldown 10` |
| `FRAME_DELAY` | seconds after the movement began, for the alarm's frame | `0.5` |
| `BURST`, `FRAME_GAP` | more frames for the page after the alarm, and the seconds between them | `3`, `0.5` |
| `ALARM_EVERY` | seconds between alarms while something keeps moving | `30` |
| `ALARMS_PER_DAY` | alarms a day before a notice and a pause until midnight | `200` |
| `WARMUP` | seconds after the camera starts in which movement is ignored | `10` |
| `KEEP_DAYS` | days to keep motion photos | `7` |

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
- **Another machine:** clone this repo there as in "Set it up", and run
  `sudo /opt/homelab/src/install alarm --topic` (it asks for the topic).
  It installs only the command; the same topic is the same place on your phone.
- **A caller handles failure itself:** `alarm … || echo "alarm not sent" >&2`. Don't hide it.
- **Somewhere that can't run the command** sends the same fields to the topic over HTTPS (ntfy's
  API: `Title`, `Priority`, `Tags`, `Click`, and the message as the body). There the topic is a
  secret like any key.

## With Shipify

Homelab shares homepi with a Shipify box. They don't touch:

- **Shipify talks; homelab alarms.** Shipify's work and replies stay in Shipify's chats, and
  nothing of Shipify calls `alarm`. Shipify can change this repo by a PR (`homelab: …`), tested by
  its CI; your merge is the approval, and the machine installs it the next morning (Updates).
- **Its own user, folders and services:** `homelab`; `/opt/homelab`, `/etc/homelab`,
  `/var/lib/homelab`; `homelab-*`. Each service is sandboxed: no view of `/home` or `/srv`, and
  it writes only to its own folder.

## Updates, and removing it

- **Updates come by themselves,** daily at about 04:30: a change merged on `main` is installed the
  way you would by hand (your merge is the approval). If only docs or tests changed, nothing
  restarts. You get a quiet "Homelab updated", or a loud alarm saying why it couldn't; a failed
  update is tried again the next day, and the version running stays as it was.
- **Now, not at 04:30:** `sudo systemctl start homelab-update`. **Never:**
  `sudo systemctl disable --now homelab-update.timer`.
- **Don't edit `/opt/homelab/src`:** it follows `main`, and a change made there stops the updates
  (the alarm says so). Changes go by a PR.
- **Remove:** `sudo /opt/homelab/src/install remove` takes away the services, page, programs, this
  copy, settings, topic, photos, user and group. The build packages stay.

## When something's wrong

| You see | Do |
|---|---|
| No alarms at all | Subscribed to the topic in ntfy? Muted? Camera on? Running the install again at the machine sends a test alarm |
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
  give `install --topic` its address: `https://your.server/topic`.
- **Pixel motion,** not people: light changes and pets can trip it. `--zones` and `--motion` tune it.

## What's where

| | |
|---|---|
| `install` | the one command: set up, `alarm`, `remove` |
| `bin/alarm` | the alarm command |
| `lib/camera-run` | starts the camera program (only while the camera is on) |
| `lib/motion-send` | sends a new motion photo as an alarm |
| `lib/check` | the minute check: camera health and old photos |
| `lib/status` | the page's status: written by the check, a new photo and the switch |
| `defaults.conf` | homelab's settings, before this machine's own |
| `lib/camera-switch`, `lib/api` | the camera's switch, and the page's way to it |
| `lib/firewall` | the rule that keeps other users here out |
| `lib/update` | the daily update |
| `systemd/` | the services: `homelab-camera` (and its path: on when the camera is), `homelab-motion` (path), `homelab-check` (timer), `homelab-api` (socket), `homelab-firewall`, `homelab-update` (timer) |
| `www/index.html` | the page |
| `test/run` | the tests, against a stand-in for ntfy and the camera |
