"""CPU encoder/decoder checks; no Isaac/Quest or existing recording is touched."""
import json
from pathlib import Path
import tempfile
import unittest
import threading
from unittest.mock import patch
import imageio_ffmpeg
import numpy as np
from episode_video import EpisodeVideo,CAMERAS
from convert_video_wallclock import convert

class VideoTest(unittest.TestCase):
    def test_regular_and_irregular_timing(self):
        for stamps,end in [([0,.2,.4,.6,.8],1.),([.08,.11,1.2,2.5,17.,59.9],60.),([0,.001,.002,.1],.25)]:
            with self.subTest(stamps=stamps),tempfile.TemporaryDirectory() as tmp:
                now=[100.]
                video=EpisodeVideo(Path(tmp)/'episode','episode',.04,clock=lambda:now[0])
                for i,stamp in enumerate(stamps):
                    frame=np.full((244,244,3),30+i*30,dtype=np.uint8)
                    video.submit({k:frame for k in CAMERAS},i,100+stamp,i*.04)
                now[0]=100+end
                report=video.close()
                self.assertIs(video.close(),report)
                self.assertIsNone(report['error'])
                self.assertLessEqual(abs(report['mp4_duration_s']-end),.040001)
                self.assertEqual(report['actual_recording_duration_s'],end)
                rows=[json.loads(line) for line in (video.directory/'frames.jsonl').read_text().splitlines()]
                self.assertEqual(len(rows),len(stamps))
                self.assertEqual(report['output_frames'],report['blank_frames']+sum(r['output_frame_count'] for r in rows))
                self.assertEqual(report['duplicate_frames'],sum(max(0,r['output_frame_count']-1) for r in rows))
                reader=imageio_ffmpeg.read_frames(str(video.directory/'video.mp4'),pix_fmt='rgb24');header=next(reader)
                decoded=0
                try:
                    for index,raw in enumerate(reader):
                        pixel=np.frombuffer(raw,dtype=np.uint8).reshape(256,768,3)[100,100,0]
                        row=next((r for r in rows if r['output_frame_start']<=index<r['output_frame_start']+r['output_frame_count']),None)
                        expected=0 if row is None else 30+row['sample_index']*30
                        self.assertLess(abs(int(pixel)-expected),6) # codec tolerance; no interpolated motion
                        decoded+=1
                finally:reader.close()
                self.assertEqual(decoded,report['output_frames'])
                self.assertAlmostEqual(decoded/header['fps'],report['mp4_duration_s'])
                print('WALLCLOCK_DECODE',json.dumps(dict(stamps=stamps,actual=end,mp4=decoded/header['fps'],frames=decoded,duplicates=report['duplicate_frames'],blank=report['blank_frames'])))

    def test_queue_drops_hold_until_wall_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate=threading.Event();encode=EpisodeVideo._encode;now=[100.]
            with patch.object(EpisodeVideo,'_encode',lambda v:(gate.wait(),encode(v))):
                video=EpisodeVideo(Path(tmp)/'episode','episode',.04,capacity=2,clock=lambda:now[0])
                frames={k:np.zeros((244,244,3),dtype=np.uint8) for k in CAMERAS}
                for i in range(4):video.submit(frames,i,100+i*.1,i*.04)
                now[0]=101.;gate.set();report=video.close()
            self.assertEqual(report['queue_dropped'],2)
            self.assertEqual(report['retained_source_frames'],2)
            self.assertEqual(report['original_frames'],4)
            self.assertEqual(report['output_frames'],25)
            self.assertEqual(report['mp4_duration_s'],1.)
            self.assertIsNone(report['error'])

    def test_legacy_conversion_preserves_originals(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);writer=imageio_ffmpeg.write_frames(str(d/'video.mp4'),(768,256),fps=25,codec='libx264',macro_block_size=1)
            writer.send(None)
            for value in (30,100,180):writer.send(np.full((256,768,3),value,dtype=np.uint8))
            writer.close()
            (d/'video.json').write_text(json.dumps(dict(time_basis='simulation_time',encoded=3,error=None)))
            (d/'frames.jsonl').write_text(''.join(json.dumps(dict(video_frame=i,sample_index=i,wall_monotonic=t,simulation_time=i*.04))+'\n' for i,t in enumerate([10.,10.12,10.5])))
            before={p.name:p.read_bytes() for p in d.iterdir()}
            report=convert(d,end=11.)
            self.assertEqual(report['mp4_duration_s'],1.)
            for name,data in before.items():self.assertEqual((d/name).read_bytes(),data)
            with self.assertRaises(FileExistsError):convert(d)
            reader=imageio_ffmpeg.read_frames(str(d/'video_wallclock.mp4'),pix_fmt='rgb24');next(reader)
            try:self.assertEqual(sum(1 for _ in reader),25)
            finally:reader.close()

if __name__=='__main__':unittest.main()
