"""CPU-only launch/path/signal checks; Docker is replaced by a local test adapter."""
import argparse
import ast
import csv
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import record_quest_base as launch
from quest_diagnostic.practice_options import add_arguments, options
from tools.toast_recording_metadata import DEFAULT_MANIFEST, validate_recording_args
from tools.view_make_toast_scenario import add_group_arguments


class BaseRecordingLaunchTests(unittest.TestCase):
    def test_command_is_accepted_by_actual_teleop_parser_and_recording_contract(self):
        # Execute only the CLI declaration block, without importing/starting Isaac.
        tree = ast.parse((ROOT / 'scripts/quest_diagnostic/teleop_toast.py').read_text())
        declarations = []
        collecting = False
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'parser':
                collecting = True
            if collecting:
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute) and node.value.func.attr == 'parse_known_args':
                    break
                declarations.append(node)
        self.assertTrue(declarations)
        namespace = dict(argparse=argparse, Path=Path, DEFAULT_MANIFEST=DEFAULT_MANIFEST,
                         add_group_arguments=add_group_arguments, add_arguments=add_arguments,
                         __doc__='CPU CLI contract')
        exec(compile(ast.Module(body=declarations, type_ignores=[]), '<teleop CLI declarations>', 'exec'), namespace)
        for index in (1, 2, 25):
            plan = launch.build_plan('operator_B_1', index)
            args = namespace['parser'].parse_args(plan['command'][4:])
            args.scenario_manifest = str(ROOT / args.scenario_manifest)
            self.assertEqual(launch.resolve_selection(args), plan['scenario_id'])
            validate_recording_args(args)
            control = options(args)
            self.assertEqual(control['position_scale'], 1)
            self.assertEqual(control['rotation_scale'], 1)
            self.assertIsNone(control['workspace_min'])
            self.assertIsNone(control['linear_speed'])

    def test_indices_and_group_storage_follow_actual_assignment(self):
        with (ROOT / 'scenario_delivery_base/assignments.csv').open() as stream:
            rows = list(csv.DictReader(stream))
        for group in launch.GROUPS:
            for index in (1, 2, 25):
                with self.subTest(group=group, index=index):
                    plan = launch.build_plan(group, index)
                    row = next(r for r in rows if r['scenario_group'] == group
                               and int(r['group_index']) == index)
                    self.assertEqual(plan['scenario_id'], row['scenario_id'])
                    self.assertEqual(plan['operator_index'], int(row['operator_index']))
                    command = plan['command']
                    self.assertEqual(command[command.index('--group_index') + 1], str(index))
                    self.assertEqual(command[command.index('--scenario_group') + 1], group)
                    relative = Path(plan['host_run']).relative_to(ROOT)
                    self.assertEqual(Path(plan['container_run']), launch.CONTAINER_ROOT / relative)
                    self.assertEqual(relative.parts[1], 'quest_base_' + group[9:].replace('_', ''))
                    self.assertEqual(relative.parts[2], f'episode_{index:03d}')
                    self.assertEqual(plan['container_bridge'], '/workspace/cyclo_lab/logs/quest_toast_recording')
                    self.assertFalse(Path(plan['host_run']).exists())

    def test_dry_run_and_invalid_inputs_do_not_create_runs(self):
        before = set((ROOT / 'recordings').glob('quest_base_*/episode_*/*'))
        env = dict(os.environ, GROUP='operator_B_1', INDEX='2')
        command = [sys.executable, '-B', str(ROOT / 'scripts/record_quest_base.py'), '--dry-run']
        result = subprocess.run(command, env=env, cwd='/tmp', text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout)['scenario_id'], 'toast_base_20261109_091')
        for value in ('0', '26', '-1', '1.5', 'bad'):
            result = subprocess.run(command + ['--index', value], env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 2)
        result = subprocess.run(command, env=dict(env, GROUP='operator_B'), text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(before, set((ROOT / 'recordings').glob('quest_base_*/episode_*/*')))

    def test_preserved_arguments_and_fresh_record_directory(self):
        first, second = launch.build_plan('operator_B_1', 1), launch.build_plan('operator_B_1', 1)
        self.assertNotEqual(first['host_run'], second['host_run'])
        cmd = first['command']
        self.assertEqual(cmd[:4], ['bash', 'scripts/run_mj.sh', '--gui', 'scripts/quest_diagnostic/teleop_toast.py'])
        self.assertNotIn('--headless', cmd)
        for flag in ('--keep-open', '--enable-grippers', '--no-home-limits', '--no-speed-limits'):
            self.assertIn(flag, cmd)
        for key, value in {'--control-profile': 'practice', '--position-scale': '1', '--rotation-scale': '1',
                           '--workspace': 'off', '--max-target-lead': '0.12', '--max-angular-lead-deg': '45',
                           '--tracking-stall-seconds': '2', '--preview-hz': '15', '--seed': '1',
                           '--record-seconds': '0', '--scenario_manifest': 'scenario_delivery_base/manifest.json',
                           '--record-dir': first['container_run'] + '/recording',
                           '--diagnostic-log': first['container_run'] + '/diagnostic.jsonl'}.items():
            self.assertEqual(cmd[cmd.index(key) + 1], value)
        with tempfile.TemporaryDirectory() as tmp:
            first['host_run'] = str(Path(tmp) / 'episode_001/run_test')
            run = launch.create_run(first)
            self.assertFalse((run / 'recording').exists())
            self.assertFalse((run / 'diagnostic.jsonl').exists())
            with self.assertRaises(FileExistsError):
                launch.create_run(first)

    def test_exit_code_and_tee_drain(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            code = launch.run_pipeline([sys.executable, '-c',
                'import sys;print("FINAL_STDOUT");print("FINAL_STDERR",file=sys.stderr);sys.exit(7)'], run, ROOT)
            self.assertEqual(code, 7)
            self.assertEqual((run / 'exit_code').read_text(), '7\n')
            self.assertIn('FINAL_STDERR', (run / 'run.log').read_text())
            self.assertIn('FINAL_STDOUT', (run / 'run.log').read_text())

    def test_interrupts_through_real_wrapper_and_relay_with_mock_docker(self):
        for phase, sig in [('initializing', signal.SIGINT), ('WAITING', signal.SIGINT),
                           ('RUNNING', signal.SIGINT), ('RUNNING', signal.SIGTERM)]:
            with self.subTest(phase=phase, sig=sig), tempfile.TemporaryDirectory() as tmp:
                d = Path(tmp)
                (d / 'Xauthority').touch()
                (d / 'probe.py').write_text('''import os,sys,time
from pathlib import Path
sys.path.insert(0,os.environ['TEST_TOOLS'])
from graceful_shutdown import Shutdown
stop=Shutdown();stop.install()
d=Path(os.environ['TEST_RUN'])
(d/'boot').touch()
if os.environ['TEST_PHASE']=='initializing':time.sleep(.4)
(d/'pid').write_text(str(os.getpid()))
print('READY '+os.environ['TEST_PHASE'],flush=True)
while not stop.requested:time.sleep(.01)
time.sleep(.15)
stop.step('save',lambda:(d/'saved').write_text(stop.reason))
stop.step('app',lambda:print('FINAL_CLEANUP_COMPLETE',flush=True))
''')
                (d / 'docker').write_text('''#!/usr/bin/env python3
import os,sys,subprocess,signal,json
from pathlib import Path
d=Path(os.environ['TEST_RUN'])
if sys.argv[1]=='exec':
 assert sys.argv[2]==(d/'container_name').read_text()
 sig=signal.SIGTERM if 'kill -s TERM' in sys.argv[-1] else signal.SIGINT
 try:os.kill(int((d/'pid').read_text()),sig)
 except (FileNotFoundError,ProcessLookupError):sys.exit(1)
else:
 assert '-T' in sys.argv and '--name' in sys.argv and '--group_index' in sys.argv
 (d/'container_name').write_text(sys.argv[sys.argv.index('--name')+1])
 (d/'docker_args.json').write_text(json.dumps(sys.argv))
 sys.exit(subprocess.call([sys.executable,str(d/'probe.py')]))
''')
                (d / 'docker').chmod(0o755)
                env = dict(os.environ, PATH=tmp + ':' + os.environ['PATH'], TEST_RUN=tmp,
                           TEST_TOOLS=str(ROOT / 'scripts/tools'), TEST_PHASE=phase,
                           DISPLAY=':test', XAUTHORITY=str(d / 'Xauthority'))
                code = ('import sys;from pathlib import Path;'
                        f'sys.path.insert(0,{str(ROOT / "scripts")!r});import record_quest_base as m;'
                        "p=m.build_plan('operator_B_1',2);"
                        f'p["host_run"]={str(d / "run")!r};r=m.create_run(p);'
                        'sys.exit(m.run_pipeline(p["command"],r,m.ROOT))')
                with (d / 'console.log').open('w') as output:
                    proc = subprocess.Popen([sys.executable, '-B', '-c', code], env=env,
                                            stdout=output, stderr=output, start_new_session=True)
                    try:
                        deadline = time.monotonic() + 10
                        ready = d / ('boot' if phase == 'initializing' else 'pid')
                        while not ready.exists() and time.monotonic() < deadline:
                            time.sleep(.02)
                        self.assertTrue(ready.exists(), (d / 'console.log').read_text())
                        # A terminal signal reaches the launcher's session, not tee or Compose.
                        os.killpg(proc.pid, sig)
                        time.sleep(.03)
                        os.killpg(proc.pid, sig)
                        proc.wait(timeout=12)
                        self.assertEqual(proc.returncode, 0, (d / 'console.log').read_text())
                        self.assertEqual((d / 'saved').read_text(), 'signal_' + sig.name)
                        self.assertEqual((d / 'run/exit_code').read_text(), '0\n')
                        self.assertIn('FINAL_CLEANUP_COMPLETE', (d / 'run/run.log').read_text())
                        self.assertEqual(json.loads((d / 'run/launcher_result.json').read_text())['tee_exit_code'], 0)
                        argv = json.loads((d / 'docker_args.json').read_text())
                        self.assertEqual(argv[argv.index('--group_index') + 1], '2')
                        self.assertIn('DISPLAY=:test', argv)
                    finally:
                        if proc.poll() is None:
                            proc.kill()
                            proc.wait()


if __name__ == '__main__':
    unittest.main()
