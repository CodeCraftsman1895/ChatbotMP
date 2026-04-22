# from youtube_transcript_api import YouTubeTranscriptApi  <-- Moved inside function
import re

def extract_youtube(link: str) -> dict:
    """
    Extract transcript text from a YouTube video URL.

    Args:
        link (str): YouTube video URL.

    Returns:
        dict: {"content": str, "error": str or None}
    """
    if not link or not isinstance(link, str):
        return {"content": "", "error": "Invalid or missing link"}
    
    try:
        # Extract video ID from various YouTube URL formats
        match = re.search(r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([0-9A-Za-z_-]{11})', link)
        if not match:
            return {"content": "", "error": f"Invalid YouTube URL format: {link}"}
        video_id = match.group(1)
        
        from youtube_transcript_api import YouTubeTranscriptApi
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        
        # Try to find English transcript first
        try:
            transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB', 'en-IN'])
        except Exception:
            # If no English, try Hindi and translate to English
            try:
                transcript = transcript_list.find_transcript(['hi'])
                transcript = transcript.translate('en')
            except Exception as e:
                return {"content": "", "error": f"No suitable transcript found for {link}: {e}"}
        
        data = transcript.fetch()
        text = " ".join([t.text for t in data])
        return {"content": text, "error": None}
    except Exception as e:
        return {"content": "", "error": f"YouTube extraction failed for {link}: {e}"}