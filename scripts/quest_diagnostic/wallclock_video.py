"""CFR sample-and-hold from monotonic sample timestamps; no motion interpolation."""
import math
import time
import imageio_ffmpeg
import numpy as np

class WallClockWriter:
    FPS=25.

    def __init__(self,path,start,emit):
        self.start=start;self.emit=emit;self.frame_count=0;self.blank_frames=0
        self.duplicates=0;self.omitted_sources=0;self.pending=None;self.last=start
        self.writer=imageio_ffmpeg.write_frames(str(path),(768,256),fps=self.FPS,
            codec='libx264',pix_fmt_in='rgb24',pix_fmt_out='yuv420p',macro_block_size=1,
            output_params=['-crf','22','-preset','veryfast','-threads','2','-movflags','+faststart'])
        self.writer.send(None)

    def tick(self,stamp):
        if not math.isfinite(stamp) or stamp<self.last:raise ValueError('Non-monotonic or pre-start video timestamp')
        self.last=stamp
        return max(0,math.ceil((stamp-self.start)*self.FPS-1e-7))

    def advance(self,stamp):
        end=self.tick(stamp);first=self.frame_count;count=end-first
        atlas,row=self.pending if self.pending else (np.zeros((256,768,3),dtype=np.uint8),None)
        began=time.monotonic()
        for _ in range(count):self.writer.send(atlas);self.frame_count+=1
        if row is None:self.blank_frames+=count
        else:
            row.update(video_frame=first,presentation_time=first/self.FPS,
                output_frame_start=first,output_frame_count=count,
                duplicate_frames=max(0,count-1),omitted_from_output=count==0,
                timing_policy='hold this source sample until next sample/end; no interpolation',
                ffmpeg_send_ms=(time.monotonic()-began)*1000)
            self.duplicates+=max(0,count-1);self.omitted_sources+=int(count==0)
            self.emit(row)

    def add(self,atlas,row):
        self.advance(row['wall_monotonic'])
        self.pending=(atlas,row)

    def finish(self,end):
        self.advance(end);self.pending=None

    def close(self):self.writer.close()
