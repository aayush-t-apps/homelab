# Home setup: the laptop runs Shipify, the Pi runs homelab

The plan for the home machines, and the steps to get there. Nothing here is installed yet: each
step is yours to run. Written 2026-10-23.

## The layout

| Machine | Job | Why |
|---|---|---|
| **Old x86 laptop** (32 GB RAM, SSD, few cores) | the Shipify box: all its runner slots | faster x86 cores and an internal SSD: clones, builds and tests run faster than on the Pi |
| **Raspberry Pi 4, 8 GB** (homepi) | homelab only: the camera, the page, `alarm` | small, quiet, about 3–5 W at idle, and near the camera |

- **Separation:** a Shipify task can't slow the camera, and a camera problem can't stop a task.
- **No code change:** Shipify takes the next run on any free slot on any box. Moving the slots is
  only `box add` and `box remove`.

## 1. Prepare the laptop

1. **Disk:** install Ubuntu Server 24.04 LTS (no desktop) on the SSD. `box add` refuses other
   OSes. Remove the HDD, or keep it out of the runner's path (backups only): many small reads and
   writes are slow on an HDD, and a spinning disk that runs all the time can fail.
2. **Check the SSD first:** `sudo smartctl -a /dev/<ssd>` (package `smartmontools`). Look at the
   wear and the reallocated or pending sectors. A worn SSD is not worth the setup.
3. **Always on:**
   - BIOS: **power on after AC loss**, if it has it.
   - Lid closed does nothing: in `/etc/systemd/logind.conf`, set `HandleLidSwitch=ignore` and
     `HandleLidSwitchExternalPower=ignore`, then `sudo systemctl restart systemd-logind`.
   - Battery: a charge limit of 60–80% if the BIOS has one. A battery kept full all the time can
     swell. Without a limit, check it now and then, or take it out if the laptop runs without it.
4. **Network:** Ethernet, not Wi-Fi. `sudo apt install openssh-server`, SSH keys only.

## 2. Make it the Shipify box

From your PC, as Shipify's [box setup](https://github.com/aayush-t-apps/shipify/blob/main/docs/box-setup.md)
says (it has the details; this page doesn't copy them):

```
pnpm ship box add <user>@<laptop> --slots <cores> --manage        # shows the plan
pnpm ship box add <user>@<laptop> --slots <cores> --manage --yes  # does it
```

- **Slots = the laptop's core count** (`nproc`). At 32 GB, memory is no limit (a busy slot needs
  about 1.6 GB); cores are. Past the cores, checks that overlap get slower, but get no more done.
- **More slots use your Claude plan faster:** 4 tasks at once use its limits 4 times as fast. For
  one person, 2 to 4 slots in all is usually enough.
- `--manage` adds Tailscale, Cockpit and a firewall.
- **Measure it:** `bash box/load-test.sh <app folder> 1 2 3 4` on the laptop prints each run's time
  and memory. Lower the slots if a higher count gets no faster.

## 3. Switch over in one go

1. Run one task end to end on the laptop, and check that it finishes.
2. Take the Pi's slots away: `pnpm ship box remove homepi --yes`, then on the Pi
   `sudo systemctl disable --now shipify-box-homepi shipify-box-homepi-2 shipify-box-homepi-3`.
3. Check: `systemctl list-units 'shipify-box-*'` on the Pi lists nothing.

No old runner is left behind. **The other choice:** keep homepi at 1 slot as a backup
(`pnpm ship box add <user>@homepi --slots 1 --manage --yes`), so tasks still run when the laptop
is off. It costs a little power and one more box to watch.

## 4. The Pi after the move

Homelab only, as it runs today. Measured on 2026-10-23: the camera program uses about 4% of one
core and about 20 MB of memory; the rest starts only when it's needed. With the camera off,
nothing runs for it. The Pi has much more than homelab needs. That is headroom, not waste: a
smaller board costs money and saves only 1–2 W.

## Later, if you want (none of it is set up)

Each one is optional. Each one that runs all the time on the Pi needs your yes first
([AGENTS.md](../AGENTS.md)).

| Idea | What it gives | Cost |
|---|---|---|
| **Laptop watch** | a timer on the Pi pings the laptop and sends an `alarm` if it's offline. Shipify's own watch already tells you in Shipify after 4 minutes; this one reaches your phone | a homelab change (a PR) and one small timer |
| **Ad and tracker blocking** (AdGuard Home or Pi-hole) | fewer ads and trackers on every device at home | about 100 MB of memory, a new service, and your router's DNS set to the Pi |
| **Tailscale exit node or subnet router** | safe internet on public Wi-Fi, and your home devices from anywhere | a setting in Tailscale, almost no load |
| **Home Assistant** | one place for smart plugs, lights and sensors, and the camera | only worth it with smart devices; 1–2 GB of memory |
| **A second camera** | another view | homelab is one camera per machine: a second small machine, or a change to homelab |
| **A backup Shipify slot** | tasks run when the laptop is off | about 1.6 GB while busy (step 3, the other choice) |
| **Sell the Pi** | money back | the camera must then move to the laptop, which must stay near it and on |
