import os, subprocess, tempfile

with tempfile.TemporaryDirectory() as d:
    src=os.path.join(d,"src.mp4"); dst=os.path.join(d,"dst.mp4")
    make=["ffmpeg","-y","-loglevel","error","-f","lavfi","-i","color=c=black:s=320x180:d=1","-c:v","libx264","-pix_fmt","yuv420p",src]
    assert subprocess.run(make).returncode==0, "ffmpeg input fixture failed"
    cmd=["ffmpeg","-y","-loglevel","error","-i",src,"-map","0:v:0","-map","0:a?","-c:v","libx264","-preset","veryfast","-crf","23","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k","-movflags","+faststart",dst]
    assert subprocess.run(cmd).returncode==0, "canonical transcode failed"
    assert os.path.getsize(dst)>0, "transcoded output empty"
print("V5.17 media fallback test: PASS")
