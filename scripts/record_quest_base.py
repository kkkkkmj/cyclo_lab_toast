#!/usr/bin/env python3
"""Launch one base-set Quest run without reusing any recording directory.

GROUP/INDEX select both the scenario and its storage directory. --dry-run resolves
the real assignment and prints the complete plan without creating files or Docker
processes. Run this host-side script, not inside the simulation container.
"""
import argparse
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import sys
import time
import uuid

from tools.view_make_toast_scenario import GROUPS, resolve_selection

ROOT = Path(__file__).resolve().parents[1]
CONTAINER_ROOT = Path('/workspace/cyclo_lab')
MANIFEST = Path('scenarios/fixed_tpb/manifest.json')
BRIDGE = Path('logs/quest_toast_recording')


def build_plan(group, index, root=ROOT):
    """Use the GUI/Quest selector and the selected manifest's assignment CSV."""
    if group not in GROUPS or type(index) is not int or not 1 <= index <= 25:
        raise ValueError('Expected a subgroup and INDEX in 1..25')
    root = Path(root).resolve()
    args = argparse.Namespace(scenario_manifest=str(root / MANIFEST),
                              scenario_group=group, group_index=index,
                              operator=None, scenario_index=None, scenario_id=None)
    scenario_id = resolve_selection(args)
    tag = group.removeprefix('operator_').replace('_', '')
    name = 'run_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + uuid.uuid4().hex[:12]
    relative = Path('recordings') / ('quest_base_' + tag) / f'episode_{index:03d}' / name
    host_run, container_run = root / relative, CONTAINER_ROOT / relative
    command = [
        'bash', 'scripts/run.sh', '--gui', 'scripts/quest_diagnostic/teleop_toast.py',
        '--keep-open', '--enable-grippers', '--control-profile', 'practice',
        '--scenario_manifest', str(MANIFEST), '--scenario_group', group, '--group_index', str(index),
        '--bridge-dir', str(CONTAINER_ROOT / BRIDGE),
        '--position-scale', '1', '--rotation-scale', '1',
        '--no-home-limits', '--no-speed-limits', '--workspace', 'off',
        '--max-target-lead', '0.12', '--max-angular-lead-deg', '45',
        '--tracking-stall-seconds', '2', '--preview-hz', '15', '--seed', '1',
        '--record-dir', str(container_run / 'recording'), '--record-seconds', '0',
        '--diagnostic-log', str(container_run / 'diagnostic.jsonl'),
    ]
    return dict(schema_version=1, scenario_manifest=str(MANIFEST),
                manifest_sha256=hashlib.sha256((root / MANIFEST).read_bytes()).hexdigest(),
                scenario_group=group, group_index=index, operator=args.operator,
                operator_index=args.scenario_index, scenario_id=scenario_id,
                host_root=str(root), host_run=str(host_run), container_run=str(container_run),
                host_bridge=str(root / BRIDGE), container_bridge=str(CONTAINER_ROOT / BRIDGE),
                command=command, shell_command=shlex.join(command),
                log_command=['tee', '-i', str(host_run / 'run.log')])


def create_run(plan):
    """Reserve a fresh run only; the recorder creates recording/ itself."""
    run = Path(plan['host_run'])
    run.parent.mkdir(parents=True, exist_ok=True)
    run.mkdir()  # Fail on a collision; never reuse or truncate an existing run.
    with (run / 'launch.json').open('x') as stream:
        json.dump(dict(plan, launcher_pid=os.getpid()), stream, indent=2)
        stream.write('\n')
    return run


def run_pipeline(command, run, cwd):
    """Keep tee alive through Ctrl+C and wait for the existing relay's cleanup.

    Both children have separate sessions. Terminal signals reach this launcher,
    which forwards the first request to its own run_mj/relay PID only. The relay
    handles container/Python PID readiness. No timeout or forced kill is used.
    exit_code is the run_mj return code, equivalent to Bash PIPESTATUS[0].
    """
    requested = []

    def request(sig, frame):
        if not requested:
            requested.append(sig)

    previous = {sig: signal.signal(sig, request) for sig in (signal.SIGINT, signal.SIGTERM)}
    child = tee = None
    code = 127
    tee_code = 0
    try:
        with (run / 'run.lock').open('x') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            lock.write(str(os.getpid()) + '\n')
            lock.flush()
            # Reserve the log before starting either child; tee sees a new empty file.
            with (run / 'run.log').open('x'):
                pass
            try:
                tee = subprocess.Popen(['tee', '-i', str(run / 'run.log')],
                                       stdin=subprocess.PIPE, start_new_session=True)
                if requested:
                    code = 128 + requested[0]
                else:
                    child = subprocess.Popen(command, cwd=cwd, stdout=tee.stdin,
                                             stderr=subprocess.STDOUT, start_new_session=True)
                    tee.stdin.close()
                    sent = False
                    while child.poll() is None:
                        if requested and not sent:
                            try:
                                child.send_signal(requested[0])
                            except ProcessLookupError:
                                pass
                            sent = True
                        time.sleep(0.05)
                    code = child.wait()
                    if code < 0:
                        code = 128 - code
            except OSError as error:
                with (run / 'run.log').open('a') as stream:
                    stream.write(f'LAUNCH_ERROR {error}\n')
                print(f'Launch failed: {error}', file=sys.stderr)
            finally:
                if tee is not None:
                    if not tee.stdin.closed:
                        tee.stdin.close()
                    tee_code = tee.wait()
                with (run / 'exit_code').open('x') as stream:
                    stream.write(str(code) + '\n')
                with (run / 'launcher_result.json').open('x') as stream:
                    json.dump(dict(run_exit_code=code, tee_exit_code=tee_code,
                                   requested_signal=(signal.Signals(requested[0]).name
                                                     if requested else None)), stream, indent=2)
                    stream.write('\n')
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    # Preserve the simulation exit code on disk and surface a logging failure too.
    return code if code else (1 if tee_code else 0)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--group', choices=GROUPS, default=os.environ.get('GROUP', 'operator_B_1'))
    parser.add_argument('--index', type=int, default=os.environ.get('INDEX', '1'))
    parser.add_argument('--dry-run', action='store_true', help='Print resolved paths/arguments; create nothing')
    args = parser.parse_args(argv)
    try:
        plan = build_plan(args.group, args.index)
    except (ValueError, KeyError, OSError) as error:
        parser.error(str(error))
    if args.dry_run:
        print(json.dumps(plan, indent=2))
        return 0
    if not os.environ.get('DISPLAY'):
        parser.error('Set DISPLAY to your active desktop display before GUI recording')
    authority = Path(os.environ.get('XAUTHORITY', str(Path.home() / '.Xauthority')))
    if not authority.is_file():
        parser.error('Set XAUTHORITY to your existing desktop cookie file')
    if any(shutil.which(name) is None for name in ('bash', 'docker', 'tee')):
        parser.error('Host bash, Docker and tee are required')
    run = create_run(plan)
    print(f"SCENARIO_PLAN group={args.group} group_index={args.index} scenario_id={plan['scenario_id']}", flush=True)
    print(f'RUN_DIR={run}', flush=True)
    print(f"CONTAINER_RUN={plan['container_run']}", flush=True)
    result = run_pipeline(plan['command'], run, ROOT)
    print(f'RUN_EXIT={result} exit_code_file={run / "exit_code"}', flush=True)
    return result


if __name__ == '__main__':
    sys.exit(main())
