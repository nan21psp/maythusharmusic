# maythusharmusic/utils/thumbnails.py

import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from youtubesearchpython.__future__ import VideosSearch
import config  # Config မှ ပုံယူရန်

def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage

def truncate(text):
    list = text.split(" ")
    text1 = ""
    text2 = ""    
    for i in list:
        if len(text1) + len(i) < 30:        
            text1 += " " + i
        elif len(text2) + len(i) < 30:      
            text2 += " " + i
    text1 = text1.strip()
    text2 = text2.strip()     
    return [text1, text2]

async def get_thumb(videoid: str):
    if os.path.isfile(f"cache/{videoid}_v4.png"):
        return f"cache/{videoid}_v4.png"

    url = f"https://www.youtube.com/watch?v={videoid}"
    
    # Default Values
    title = "Music Play"
    duration = "Unknown"
    thumbnail = config.PING_IMG_URL # Default ပုံ (Error တက်ရင် သုံးရန်)
    views = "Views"
    channel = "Channel"

    try:
        results = VideosSearch(url, limit=1)
        search_result = (await results.next()).get("result")
        
        if search_result:
            result = search_result[0]
            title = result.get("title", "Music Play")
            title = re.sub("\W+", " ", title).title()
            duration = result.get("duration", "Live")
            # Thumbnail ရှာမရရင် Default ပုံကိုပဲ ဆက်သုံးမယ်
            if result.get("thumbnails"):
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            views = result.get("viewCount", {}).get("short", "Views")
            channel = result.get("channel", {}).get("name", "Channel")
    except Exception as e:
        print(f"Thumbnail Search Error for {videoid}: {e}")
        # Error တက်ရင် Default ပုံနဲ့ ဆက်လုပ်မယ် (Return မပြန်တော့ဘူး)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(f"cache/thumb{videoid}.png", mode="wb")
                    await f.write(await resp.read())
                    await f.close()
                else:
                    # Download မရရင် Default ပုံ ပြန်ပေးမယ်
                    return config.PING_IMG_URL
    except Exception:
        return config.PING_IMG_URL

    try:
        image = Image.open(f"cache/thumb{videoid}.png")
        image1 = changeImageSize(1280, 720, image)
        image2 = image1.convert("RGBA")
        background = image2.filter(filter=ImageFilter.BoxBlur(20))
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.6)
        
        draw = ImageDraw.Draw(background)
        arial = ImageFont.truetype("maythusharmusic/assets/font2.ttf", 30)
        font = ImageFont.truetype("maythusharmusic/assets/font.ttf", 30)
        title_font = ImageFont.truetype("maythusharmusic/assets/font3.ttf", 45)

        circle_thumbnail = image.resize((400, 400))
        # Circle crop logic ကို ရိုးရှင်းအောင်လုပ်ထားခြင်း (Optional)
        
        background.paste(circle_thumbnail, (120, 160))

        text_x_position = 565
        title1 = truncate(title)
        draw.text((text_x_position, 180), title1[0], fill=(255, 255, 255), font=title_font)
        draw.text((text_x_position, 230), title1[1], fill=(255, 255, 255), font=title_font)
        draw.text((text_x_position, 320), f"{channel}  |  {views}", fill=(255, 255, 255), font=arial)
        
        # Progress Bar
        draw.line([(text_x_position, 380), (1145, 380)], fill="white", width=9)
        draw.line([(text_x_position, 380), (text_x_position + 100, 380)], fill="red", width=9)
        draw.ellipse([(text_x_position + 90, 370), (text_x_position + 110, 390)], fill="red")

        draw.text((text_x_position, 400), "00:00", (255, 255, 255), font=arial)
        draw.text((1080, 400), duration, (255, 255, 255), font=arial)

        # Play Icons (File မရှိရင် Error မတက်အောင် try ခံထားပါ)
        try:
            play_icons = Image.open("maythusharmusic/assets/play_icons.png")
            play_icons = play_icons.resize((580, 62))
            background.paste(play_icons, (text_x_position, 450), play_icons)
        except:
            pass

        background_path = f"cache/{videoid}_v4.png"
        background.save(background_path)
        
        if os.path.exists(f"cache/thumb{videoid}.png"):
            os.remove(f"cache/thumb{videoid}.png")

        return background_path
        
    except Exception as e:
        print(f"Image Processing Error: {e}")
        return config.YOUTUBE_IMG_URL
