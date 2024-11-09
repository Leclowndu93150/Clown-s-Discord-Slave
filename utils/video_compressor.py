import ffmpeg
import os

async def compress_file(file_path):
    max_size = 8 * 1024 * 1024
    compressed_file_path = os.path.join(
        os.path.dirname(file_path), f"compressed_{os.path.basename(file_path)}"
    )
    bitrate = 1_000_000

    while True:
        try:
            (
                ffmpeg
                .input(file_path)
                .output(compressed_file_path, video_bitrate=bitrate, vf='scale=-1:720')
                .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as e:
            error_message = e.stderr.decode() if e.stderr else "Unknown error"
            print("An error occurred during compression:", error_message)
            break

        if os.path.getsize(compressed_file_path) <= max_size:
            break

        if bitrate > 100_000:
            bitrate -= 100_000
        else:
            break

    return compressed_file_path
