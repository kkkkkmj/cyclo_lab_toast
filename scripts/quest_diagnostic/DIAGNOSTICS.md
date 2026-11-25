# Inactive transitions and loop timing

Use the existing `--diagnostic-log` option in the [recording command](RECORDING.md).
No additional control mode or threshold is introduced. The trace also works without recording.
These observations locate candidate bottlenecks; they do not themselves establish causality or
validate PhysX/Quest tracking.

## Events in diagnostic.jsonl

| Event | Recorded fields and scope |
|---|---|
| `decision` | Existing input snapshot, controller reasons, squeeze/trigger, preview validity, reference changes, pre-step measured and commanded poses, actions and tracking monitor. Also `loop_index`, `episode_number`, and `record_sample_monotonic` for exact HDF5 timing alignment. Terminal action rows are retained even after transition to WAITING. |
| `control_transition` | Emitted on reason/active/reference changes, independently of episode termination. `before`, `after`, `previous_sample`, `changes`, `reference_events`, `stage`, and `running_inactive` distinguish an inactive transition during RUNNING from an episode stop. |
| `loop_timing` | One completed row per iteration, including WAITING, tracking-stop early continue, and final exit/exception. Wall duration, tick interval, counted simulation advance, phase/episode/control-step indices, complete performance counters, diagnostic cost and live async-video counters. |
| `preview` | Existing frame/encoding/teleop data. Its performance snapshot ends before publication; use `loop_timing` for publication and sleep costs. |
| `end` | Finalization performance and aggregate diagnostic serialization/write/flush cost. |

Transition snapshots retain per-hand `reason`, `active`, `target_enabled`, validity/input reason,
squeeze/trigger/rebase buttons, controller pose, clutch anchor and gripper commands. They also retain
input sequence/age/liveness/visibility, reference and safety epochs, preview validity/guard/status,
`reference_changes`, basis, `measured_pose`, `target_pose`, `raw_target_pose`, and `tracking_monitor`.
`active` follows the existing HUD verdict (`reason == active`); `target_enabled` additionally identifies
the existing anchored state. `rebase_requested` records a request, not a claim it was accepted.

`before` at a control update uses the new input and existing controller state; `previous_sample` retains
the preceding decision's input/state. `after` is after control/guard handling. All measured poses reuse
the existing pre-step read, timestamped by `measured_monotonic`; there is no extra post-step/GPU read.
A stop without a new pose read stores null, rather than claiming an old pose is current. Pose quaternions
are xyzw in the same frame as controller targets. Tracking-stop early exits include a transition and
loop summary even though they intentionally take no further physics step and no normal sleep.

## Timing fields

All durations below are **host wall milliseconds**, not isolated GPU kernel times.
`loop_timing.performance.wall_call_ms` contains these named call intervals; `calls` supplies counts.
A zero count means the stage did not run; a stage never called yet may be absent.

| Fields | What is measured |
|---|---|
| `input_read`, `measured_pose_read` | Bridge reads and existing wrist pose readback |
| `control_update`, `control_action`, `tracking_monitor` | Existing controller update, action construction and tracking check |
| `episode_commands`, `env_reset_total`, `record_start` | Start/stop handling, explicit reset, recorder setup; overlapping intervals |
| `env_step_total` | Complete env.step, including physics, rendering, observations, rewards/terminations, recording and possible automatic reset |
| `sim_step_call`, `render_call`, `scene_update`, `observations` | Inclusive host API calls inside the environment, with asynchronous work possibly completing in a later call |
| `process_action`, `apply_action` | Existing action-manager calls |
| `record_pre_step`, `record_post_step`, `record_pre_reset` | Inclusive recorder-manager hooks |
| `record_timing_prepare`, `record_post_step_prepare`, `record_export_prepare` | Timing-row preparation, post-step data handling, and export preparation |
| `record_video_readback`, `record_video_submit` | Existing recorded RGB/timing readback, then image copying and nonblocking queue submission on the control thread |
| `record_hdf5_export`, `record_sidecar_write`, `record_metadata_flush` | Dataset export and sidecar/metadata writes; export may also convert data and reset recorder buffers |
| `record_video_finalize_wait` | Episode-boundary worker join/finalization, on the control thread |
| `preview_camera_readback`, `preview_encode`, `preview_publish` | Existing camera update/readback, JPEG encoding, and atomic preview publication |
| `diagnostic_snapshot`, `diagnostic_transition`, `terminal_report`, `sleep` | Snapshot/event handling, terminal output, and actual sleep-call wall duration |

**Do not sum nested intervals.** `env_step_total` is the combined environment cost, not pure physics.
Even `sim_step_call` may include synchronization or other engine work. The former `physics_call`
measurement is renamed to avoid that implication; bridge/offline readers still accept old traces.
No GPU synchronization, additional render, camera query or physics step was added for timing.

`loop_wall_ms` spans loop entry through sleep and summary preparation, excluding serialization/write
of that summary itself. `previous_tick_interval_ms` includes that previous summary and intervening
loop overhead. `previous_summary_emit_ms` explicitly reports its cost on the next row.
`sleep_requested_ms` is the unchanged sleep budget; `wall_call_ms.sleep` measures actual sleep.
`diagnostic_cost_ms` reports serialization/write/flush costs before the current summary; the final
`end` event has cumulative costs. These can overlap other measured stages and must not be added twice.

`simulation.time_before_s`, `time_after_s`, and `advanced_s` use the existing Python
`env._sim_step_counter * physics_dt`. They count environment physics steps without a GPU transfer;
untracked engine reset/warmup work is excluded. Terminal iterations retain their counted advance even
when automatic reset has cleared the episode buffer. WAITING and pre-step tracking stops advance zero.
`control_steps_before/after` and `episode_before/after` describe reset boundaries separately.

## Asynchronous video

`loop_timing.async_video` samples `queue_depth`, `queue_capacity`, `queue_peak_sampled`, `submitted`,
`encoded`, `queue_dropped`, `pending_or_failed`, `error`, `worker_totals_ms` and `last_frame_ms`.
These are lightweight live snapshots; worker progress and queue depth are approximate between reads.
The queue capacity and drop policy are unchanged. Pending work is not labeled as a final dropped frame.

Each encoded row in `episode_*/frames.jsonl` additionally stores `queue_wait_ms`,
`queue_depth_at_dequeue`, `writer_start_ms`, `atlas_compose_ms`, `ffmpeg_send_ms` and `worker_frame_ms`.
`video.json.async_timing` retains final counters and worker totals, including frame-log write time
and `writer_finalize_ms`. Worker totals are episode-cumulative, separate from the control-thread
per-loop intervals. `ffmpeg_send_ms` includes pipe writes/backpressure; it does not isolate the FFmpeg
process's codec execution. Final encoder drain may happen at close. No per-frame GPU profiler is used.

## Logging overhead

JSONL uses compact serialization and a bounded 64 KiB stream buffer, with explicit flush at roughly
one-second intervals and on close (buffer capacity can trigger writes sooner). It does not flush or
fsync every row. A crash can lose buffered tail data. Detailed before/after snapshots are emitted on
transitions rather than duplicated on every unchanged decision; joint diagnostics retain the existing
2 Hz cap. The logger adds neither full image copies nor new sensor samples.
