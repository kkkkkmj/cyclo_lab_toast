# Troubleshooting

## Docker and shared hosts

The Compose configuration uses host networking/IPC and all GPUs. Check existing
containers, GPU usage and ports before launching alongside other workloads.
The inherited image/project names can collide with another Cyclo Lab deployment;
a different container name alone does not isolate GPU load or ports. Docker
includes dependency ranges and is not a fully locked build.

## Scenario settling and control

Inspect rack/bread settling before collection. Static layout constraints do not
guarantee stable contacts, robot reachability or collision-free manipulation.
The 1:1 controller target mapping does not guarantee instantaneous robot tracking.
Inspect recorded outputs before using them for training or replay.

## Quest connection and pairing

Use the PC's reachable LAN address, not localhost, and an unused port allowed by
the local firewall. Open the HTTPS URL printed by the server in Quest Browser,
accept its local HTTPS certificate and enter the single-use Pair PIN. Type `p`
and Enter in the server terminal for a new PIN. Reload the browser after changing
client/server versions. Certificates live in `~/.local/state/cyclo-quest-tls`;
do not commit private keys.

The base launcher uses `logs/quest_toast_recording` on the host and
`/workspace/cyclo_lab/logs/quest_toast_recording` in the container. The server and
simulation must use that same bridge. Run only one simulation instance per bridge directory.
Release both squeeze buttons before pressing X, then wait for `REC` / `RECORD_STARTED`.
See [recording diagnostics](../scripts/quest_diagnostic/DIAGNOSTICS.md).

## Missing assets

See [asset setup](ASSETS.md). Run `git lfs pull` and `git lfs fsck` for the rack
wrapper; restore a missing tracked `bread_slot.usdz` from the intended revision.
Run the pinned RoboDojo downloader for missing toaster/bread/plate files. A local
hash-check pass does not certify NVIDIA cloud dependencies or renderer loading.
Do not replace the rack with a different mesh or change reference hashes.

## GUI and headset display

Run from an X11 desktop session. Keep its `DISPLAY` and `XAUTHORITY` values;
`:0` and `$HOME/.Xauthority` are only fallbacks. Check that the cookie file exists
and is accessible before launching. Do not disable X authentication globally.
Keep both Compose files in the command so the host checkout is mounted correctly.

Browser display preferences persist per address. Exit VR, adjust Cast fit and
re-enter VR. PC preview does not establish the headset/casting crop. The current
HUD is `cast-fixed-14`; its default scale is 0.46, center (0.22, 0.04), margin 0.02.

## Simulator remains alive after Ctrl+C

The application can remain blocked in native code or Kit cleanup. This remains
an open issue. Preserve the run folder
and inspect `SHUTDOWN_WAIT`, the recovery log named by `MJ_RUN`, and the exact
container name printed by that same launch. Do not identify a session by a broad
process name or stop every Compose container.

```bash
# Replace with the exact container from YOUR run's MJ_RUN line.
export RUN_CONTAINER=exact-container-name-from-your-run
# Read-only inspection; run these only after setting the exact name.
docker inspect --format '{{.Name}} {{.State.Status}}' "$RUN_CONTAINER"
docker logs --tail 100 "$RUN_CONTAINER"
```

If the original console is still responsive, enter `q` and allow finalization.
If it is not, an operator may resend SIGINT to that container's registered Python
PID after confirming its identity:

```bash
docker exec "$RUN_CONTAINER" sh -c \
  'read -r pid < /tmp/cyclo-mj-python.pid; case "$pid" in ""|*[!0-9]*) exit 2;; esac; kill -INT "$pid"'
```

A native hang may still prevent cleanup. As a **last resort chosen by the
operator**, `docker stop --time 60 "$RUN_CONTAINER"` sends TERM and eventually
KILL to this one container. That can lose buffered HDF5/MP4 data: preserve all
existing run files, treat interrupted outputs as incomplete and inspect them
before use. These commands are recovery options; they do not resolve the underlying shutdown issue.

[Documentation index](README.md)
