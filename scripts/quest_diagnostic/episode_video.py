"""Bounded asynchronous encoding of recorded simulation RGB, never desktop capture."""
import json
from pathlib import Path
import queue
import threading
import time

import imageio_ffmpeg
import numpy as np
from PIL import Image
from preview_encoding import compose_native_preview
from wallclock_video import WallClockWriter

CAMERAS = ('head_cam', 'left_wrist_cam', 'right_wrist_cam')


class EpisodeVideo:
    def __init__(self, directory, episode_id, dt, capacity=32, clock=None):
        self.clock=clock or time.monotonic
        self.started_monotonic=self.clock()
        self.ended_monotonic=None
        self.output_frames=self.blank_frames=self.duplicate_frames=self.omitted_source_frames=0
        self.directory = Path(directory)
        self.directory.mkdir(exist_ok=False)
        self.episode_id = episode_id
        self.dt = dt
        self.queue = queue.Queue(maxsize=capacity)
        self.stopping = threading.Event()
        self.error = None
        self.submitted = self.dropped = self.encoded = 0
        self.closed = False
        self.max_queue_depth=0
        self.worker_totals_ms={}
        self.last_frame_timing=None
        self.thread = threading.Thread(target=self._encode, daemon=True)
        self.thread.start()

    def submit(self, images, sample_index, wall_time, simulation_time):
        """Called only for complete recorder rows, before any terminal reset."""
        self.submitted += 1
        if self.error or self.queue.full():
            self.dropped += 1
            return
        # Camera readback/copy remains on the simulation thread; no encoding or pipe writes here.
        frames = [np.array(images[name], copy=True) for name in CAMERAS]
        row = dict(sample_index=sample_index, wall_monotonic=wall_time,
                   simulation_time=simulation_time, enqueued_monotonic=time.monotonic())
        try:
            self.queue.put_nowait((frames, row))
            self.max_queue_depth=max(self.max_queue_depth,self.queue.qsize())
        except queue.Full:
            self.dropped += 1

    def _encode(self):
        writer=None
        previous=previous_readback=None
        try:
            with (self.directory/'frames.jsonl').open('x') as timestamps:
                def emit(row):
                    row['worker_frame_ms']+=row['ffmpeg_send_ms']
                    log_started=time.monotonic()
                    timestamps.write(json.dumps(row,separators=(',',':'))+'\n')
                    timings={k:row[k] for k in ('queue_wait_ms','writer_start_ms','atlas_compose_ms','ffmpeg_send_ms','worker_frame_ms')}
                    timings['frame_log_write_ms']=(time.monotonic()-log_started)*1000
                    self.worker_totals_ms={k:self.worker_totals_ms.get(k,0.)+v for k,v in timings.items()}
                    self.last_frame_timing=timings;self.encoded+=1
                while not self.stopping.is_set() or not self.queue.empty():
                    try:frames,row=self.queue.get(timeout=.05)
                    except queue.Empty:continue
                    dequeued=time.monotonic()
                    row.update(queue_wait_ms=(dequeued-row['enqueued_monotonic'])*1000,
                        queue_depth_at_dequeue=self.queue.qsize(),writer_start_ms=0.)
                    if writer is None:
                        writer=WallClockWriter(self.directory/'video.mp4',self.started_monotonic,emit)
                        row['writer_start_ms']=(time.monotonic()-dequeued)*1000
                    began=time.monotonic()
                    atlas=np.asarray(compose_native_preview([Image.fromarray(f) for f in frames]))
                    row.update(atlas_compose_ms=(time.monotonic()-began)*1000,
                        worker_frame_ms=(time.monotonic()-dequeued)*1000,
                        observation_sample_interval_s=None if previous is None else row['wall_monotonic']-previous,
                        capture_interval_s=None if previous_readback is None else row['enqueued_monotonic']-previous_readback)
                    previous=row['wall_monotonic'];previous_readback=row['enqueued_monotonic']
                    writer.add(atlas,row)
                if writer:writer.finish(self.ended_monotonic)
        except Exception as error:self.error=repr(error)
        finally:
            if writer:
                began=time.monotonic()
                try:writer.close()
                except Exception as error:self.error=repr(error)
                self.worker_totals_ms={**self.worker_totals_ms,'writer_finalize_ms':(time.monotonic()-began)*1000}
                self.output_frames=writer.frame_count;self.blank_frames=writer.blank_frames
                self.duplicate_frames=writer.duplicates;self.omitted_source_frames=writer.omitted_sources

    def status(self):
        """Nonblocking counters; queue depth/in-flight totals are approximate live snapshots."""
        return dict(episode_id=self.episode_id,queue_depth=self.queue.qsize(),queue_capacity=self.queue.maxsize,
            queue_peak_sampled=self.max_queue_depth,submitted=self.submitted,encoded=self.encoded,
            queue_dropped=self.dropped,pending_or_failed=self.submitted-self.encoded-self.dropped,
            error=self.error,worker_totals_ms=dict(self.worker_totals_ms),last_frame_ms=self.last_frame_timing,
            note='Separate worker wall time; ffmpeg_send_ms includes pipe/backpressure, not isolated codec process time. Nested timings are not additive. No extra camera readback.')

    def close(self):
        if not self.closed:
            self.ended_monotonic=self.clock()
            self.stopping.set()
            self.thread.join()  # Episode boundary only; never in the active control loop.
            self.closed = True
            report = dict(episode_id=self.episode_id, source='simulation_camera_pre_action_observations',
                          cameras=CAMERAS, fps=WallClockWriter.FPS, time_basis='wall_monotonic',
                          started_monotonic=self.started_monotonic,ended_monotonic=self.ended_monotonic,
                          actual_recording_duration_s=self.ended_monotonic-self.started_monotonic,
                          mp4_duration_s=self.output_frames/WallClockWriter.FPS,
                          duration_measurement='encoded CFR frame count / fps; independently decoded in tests',
                          output_frames=self.output_frames,original_frames=self.submitted,
                          retained_source_frames=self.encoded,
                          duplicate_frames=self.duplicate_frames,blank_frames=self.blank_frames,
                          omitted_source_frames=self.omitted_source_frames,
                          simulation_dt=self.dt,
                          playback='25fps wall-clock sample-and-hold; first frame delayed to sample time; queue gaps hold previous sample; see output_frame_start/count',
                          wall_time='wall_monotonic: pre-action sample; enqueued_monotonic: CPU readback; neither is sensor exposure time',
                          submitted=self.submitted, encoded=self.encoded,
                          dropped=self.submitted-self.encoded, queue_dropped=self.dropped,
                          error=self.error, playable=bool(self.output_frames and not self.error),
                          async_timing=self.status())
            (self.directory/'video.json').write_text(json.dumps(report, indent=2)+'\n')
            self.report = report
        return self.report
