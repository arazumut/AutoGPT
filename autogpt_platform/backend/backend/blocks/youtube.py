from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField


class YoutubeVideoTranskripsiyonBloğu(Block):
    class Girdi(BlockSchema):
        youtube_url: str = SchemaField(
            title="YouTube URL",
            description="Transkribe edilecek YouTube videosunun URL'si",
            placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        )

    class Çıktı(BlockSchema):
        video_id: str = SchemaField(description="Çıkarılan YouTube video ID'si")
        transcript: str = SchemaField(description="Videonun transkribe edilmiş metni")
        error: str = SchemaField(
            description="Transkripsiyon başarısız olursa hata mesajı"
        )

    def __init__(self):
        super().__init__(
            id="f3a8f7e1-4b1d-4e5f-9f2a-7c3d5a2e6b4c",
            input_schema=YoutubeVideoTranskripsiyonBloğu.Girdi,
            output_schema=YoutubeVideoTranskripsiyonBloğu.Çıktı,
            description="Bir YouTube videosunu transkribe eder.",
            categories={BlockCategory.SOCIAL},
            test_input={"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            test_output=[
                ("video_id", "dQw4w9WgXcQ"),
                (
                    "transcript",
                    "Never gonna give you up\nNever gonna let you down",
                ),
            ],
            test_mock={
                "get_transcript": lambda video_id: [
                    {"text": "Never gonna give you up"},
                    {"text": "Never gonna let you down"},
                ],
            },
        )

    @staticmethod
    def video_id_çıkar(url: str) -> str:
        parsed_url = urlparse(url)
        if parsed_url.netloc == "youtu.be":
            return parsed_url.path[1:]
        if parsed_url.netloc in ("www.youtube.com", "youtube.com"):
            if parsed_url.path == "/watch":
                p = parse_qs(parsed_url.query)
                return p["v"][0]
            if parsed_url.path[:7] == "/embed/":
                return parsed_url.path.split("/")[2]
            if parsed_url.path[:3] == "/v/":
                return parsed_url.path.split("/")[2]
        raise ValueError(f"Geçersiz YouTube URL'si: {url}")

    @staticmethod
    def transkript_al(video_id: str):
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            if not transcript_list:
                raise ValueError(f"Video için transkript bulunamadı: {video_id}")

            for transcript in transcript_list:
                first_transcript = transcript_list.find_transcript(
                    [transcript.language_code]
                )
                return YouTubeTranscriptApi.get_transcript(
                    video_id, languages=[first_transcript.language_code]
                )

        except Exception:
            raise ValueError(f"Video için transkript bulunamadı: {video_id}")

    def çalıştır(self, girdi_verisi: Girdi, **kwargs) -> BlockOutput:
        video_id = self.video_id_çıkar(girdi_verisi.youtube_url)
        yield "video_id", video_id

        transcript = self.transkript_al(video_id)
        formatter = TextFormatter()
        transcript_text = formatter.format_transcript(transcript)

        yield "transcript", transcript_text
