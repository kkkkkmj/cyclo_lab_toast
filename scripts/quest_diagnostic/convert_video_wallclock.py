"""Convert a completed legacy episode without changing its video or sidecars."""
import argparse
import json
from pathlib import Path
import imageio_ffmpeg
import numpy as np
from wallclock_video import WallClockWriter


def convert(directory,start=None,end=None):
    directory=Path(directory)
    old=json.loads((directory/'video.json').read_text())
    if old.get('time_basis')!='simulation_time' or old.get('error'):
        raise ValueError('Requires a completed, error-free legacy simulation_time video.json')
    rows=[json.loads(line) for line in (directory/'frames.jsonl').read_text().splitlines()]
    if not rows or len(rows)!=old['encoded']:raise ValueError('Missing/incomplete source frame timestamps')
    if [r['video_frame'] for r in rows]!=list(range(len(rows))):raise ValueError('Unexpected source video frame mapping')
    start=rows[0]['wall_monotonic'] if start is None else start
    estimated_end=end is None
    end=rows[-1]['wall_monotonic']+1/WallClockWriter.FPS if end is None else end
    if not start<=rows[0]['wall_monotonic']<=rows[-1]['wall_monotonic']<=end:raise ValueError('Invalid wall-clock bounds')
    paths=[directory/name for name in ('video_wallclock.mp4','frames_wallclock.jsonl','video_wallclock.json')]
    reserved=[]
    try:
        for path in paths:
            with path.open('x'):pass
            reserved.append(path)
    except BaseException:
        for path in reserved:path.unlink()
        raise
    reader=writer=None
    try:
        with paths[1].open('w') as output:
            writer=WallClockWriter(paths[0],start,lambda row:output.write(json.dumps(row)+'\n'))
            reader=imageio_ffmpeg.read_frames(str(directory/'video.mp4'),pix_fmt='rgb24')
            header=next(reader)
            if header['size']!=(768,256):raise ValueError('Expected native 768x256 simulation camera atlas')
            for row in rows:
                pixels=np.frombuffer(next(reader),dtype=np.uint8).reshape(256,768,3)
                writer.add(pixels,dict(row,source_video_frame=row['video_frame']))
            if next(reader,None) is not None:raise ValueError('Source video has frames missing from frames.jsonl')
            writer.finish(end);writer.close();reader.close()
        report=dict(time_basis='wall_monotonic',fps=writer.FPS,source='video.mp4',
            started_monotonic=start,ended_monotonic=end,actual_recording_duration_s=None,
            reconstructed_interval_s=end-start,mp4_duration_s=writer.frame_count/writer.FPS,
            original_frames=len(rows),output_frames=writer.frame_count,duplicate_frames=writer.duplicates,
            blank_frames=writer.blank_frames,omitted_source_frames=writer.omitted_sources,
            source_queue_dropped=old.get('queue_dropped'),
            endpoint_note='Original episode wall start/end not recoverable from frame timestamps alone. '
                +('Using first sample through last sample + 0.04s estimated tail.' if estimated_end else 'Using supplied bounds; start defaults to first sample.'),
            error=None)
        paths[2].write_text(json.dumps(report,indent=2)+'\n');return report
    except BaseException as error:
        if writer:
            try:writer.close()
            except Exception:pass
        if reader:reader.close()
        paths[2].write_text(json.dumps(dict(error=repr(error)),indent=2)+'\n')
        raise

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('episode_dir',type=Path)
    parser.add_argument('--start-wall-monotonic',type=float)
    parser.add_argument('--end-wall-monotonic',type=float)
    args=parser.parse_args()
    print(json.dumps(convert(args.episode_dir,args.start_wall_monotonic,args.end_wall_monotonic),indent=2))
