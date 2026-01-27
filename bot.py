import telebot
from telebot import types
import os
import re
import requests
import time
from datetime import datetime

TOKEN = '8547768233:AAGOuNo2gQp0kNGFTKwNkNe84BSKlhbrKM8'  # ضع التوكن الخاص بك هنا
CHANNEL_USERNAME = '@mged181'
CHANNEL_LINK = 'https://t.me/mged181'
DEVELOPER_USERNAME = 'yhdd7'  # يوزر المطور بدون @

MAX_VIDEO_SIZE_MB = 40

bot = telebot.TeleBot(TOKEN)

DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

video_info_cache = {}

# احصائيات البوت
bot_stats = {
    'total_users': set(),
    'total_downloads': 0,
    'videos_downloaded': 0,
    'slideshows_downloaded': 0,
    'failed_downloads': 0,
    'start_time': datetime.now()
}


def is_developer(message):
    """التحقق اذا المستخدم هو المطور"""
    username = message.from_user.username
    return username and username.lower() == DEVELOPER_USERNAME.lower()


def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['member', 'administrator', 'creator', 'restricted']:
            return True
        return False
    except Exception as e:
        print(f"خطأ في التحقق: {e}")
        return True


def format_number(num):
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)


def format_duration(seconds):
    """تنسيق المدة"""
    if seconds < 60:
        return f"{seconds} ثانية"
    elif seconds < 3600:
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins} دقيقة و {secs} ثانية"
    else:
        hours = seconds // 3600
        mins = (seconds % 3600) // 60
        return f"{hours} ساعة و {mins} دقيقة"


def get_file_size(url):
    """الحصول على حجم الملف بالميجابايت"""
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        size = response.headers.get('content-length')
        if size:
            return int(size) / (1024 * 1024)
    except:
        pass
    return None


def download_tikwm(url):
    """API الاول - tikwm"""
    try:
        api_url = f"https://www.tikwm.com/api/?url={url}"
        response = requests.get(api_url, timeout=30)
        data = response.json()
        
        if data.get('code') == 0:
            video_data = data['data']
            author = video_data.get('author', {})
            music = video_data.get('music_info', {})
            
            return {
                'video_id': video_data.get('id'),
                'title': video_data.get('title', 'بدون عنوان'),
                'duration': video_data.get('duration', 0),
                'create_time': video_data.get('create_time', 0),
                'region': video_data.get('region', 'غير معروف'),
                'play': video_data.get('play'),
                'hdplay': video_data.get('hdplay'),
                'wmplay': video_data.get('wmplay'),
                'music': video_data.get('music'),
                'cover': video_data.get('cover'),
                'origin_cover': video_data.get('origin_cover'),
                'dynamic_cover': video_data.get('ai_dynamic_cover'),
                'play_count': video_data.get('play_count', 0),
                'digg_count': video_data.get('digg_count', 0),
                'comment_count': video_data.get('comment_count', 0),
                'share_count': video_data.get('share_count', 0),
                'download_count': video_data.get('download_count', 0),
                'collect_count': video_data.get('collect_count', 0),
                'repost_count': video_data.get('repost_count', 0),
                'is_ad': video_data.get('is_ad', False),
                'is_commercial': video_data.get('commercialize', False),
                'images': video_data.get('images'),
                'author': {
                    'id': author.get('id'),
                    'unique_id': author.get('unique_id'),
                    'nickname': author.get('nickname'),
                    'signature': author.get('signature', ''),
                    'avatar': author.get('avatar'),
                    'avatar_larger': author.get('avatar_larger'),
                    'avatar_medium': author.get('avatar_medium'),
                },
                'music_info': {
                    'id': music.get('id'),
                    'title': music.get('title', 'غير معروف'),
                    'author': music.get('author', 'غير معروف'),
                    'album': music.get('album', 'غير معروف'),
                    'play': music.get('play'),
                    'cover': music.get('cover'),
                    'duration': music.get('duration', 0),
                    'original': music.get('original', False),
                },
            }
    except Exception as e:
        print(f"خطأ tikwm: {e}")
    return None


def download_tikcdn(url):
    """API الثاني - tikcdn"""
    try:
        api_url = "https://tikcdn.io/api/v1/post"
        response = requests.post(api_url, json={"url": url}, timeout=30)
        data = response.json()
        
        if data.get('success'):
            author_data = data.get('author', {})
            
            return {
                'video_id': data.get('id'),
                'title': data.get('description', ''),
                'duration': data.get('duration', 0),
                'create_time': data.get('create_time', 0),
                'region': 'غير معروف',
                'play': data.get('video_url'),
                'hdplay': data.get('video_url_hd'),
                'wmplay': data.get('video_url_watermark'),
                'music': data.get('audio_url'),
                'cover': data.get('cover'),
                'origin_cover': data.get('cover'),
                'dynamic_cover': None,
                'play_count': data.get('play_count', 0),
                'digg_count': data.get('like_count', 0),
                'comment_count': data.get('comment_count', 0),
                'share_count': data.get('share_count', 0),
                'download_count': data.get('download_count', 0),
                'collect_count': data.get('collect_count', 0),
                'repost_count': 0,
                'is_ad': False,
                'is_commercial': False,
                'images': data.get('images'),
                'author': {
                    'id': author_data.get('id'),
                    'unique_id': author_data.get('username'),
                    'nickname': author_data.get('nickname'),
                    'signature': author_data.get('signature', ''),
                    'avatar': author_data.get('avatar'),
                    'avatar_larger': author_data.get('avatar'),
                    'avatar_medium': author_data.get('avatar'),
                },
                'music_info': {
                    'id': data.get('music', {}).get('id'),
                    'title': data.get('music', {}).get('title', 'غير معروف'),
                    'author': data.get('music', {}).get('author', 'غير معروف'),
                    'album': 'غير معروف',
                    'play': data.get('audio_url'),
                    'cover': data.get('music', {}).get('cover'),
                    'duration': data.get('music', {}).get('duration', 0),
                    'original': data.get('music', {}).get('original', False),
                },
            }
    except Exception as e:
        print(f"خطأ tikcdn: {e}")
    return None


def get_video_data(url, max_retries=3):
    """محاولة الحصول على بيانات الفيديو من عدة مصادر"""
    apis = [download_tikwm, download_tikcdn]
    
    for attempt in range(max_retries):
        for api_func in apis:
            try:
                data = api_func(url)
                if data:
                    return data
            except Exception as e:
                print(f"محاولة {attempt + 1} فشلت: {e}")
                continue
        
        if attempt < max_retries - 1:
            time.sleep(2)
    
    return None


def download_file(url, filepath, timeout=120):
    """تحميل ملف"""
    try:
        response = requests.get(url, timeout=timeout, stream=True)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
    except Exception as e:
        print(f"خطأ تحميل: {e}")
    return False


def process_video(url):
    """معالجة وتحميل الفيديو"""
    data = get_video_data(url)
    
    if not data:
        return None, None
    
    video_id = data.get('video_id', 'unknown')
    images = data.get('images')
    
    if images and len(images) > 0:
        image_paths = []
        for i, img_url in enumerate(images):
            img_path = os.path.join(DOWNLOAD_DIR, f"{video_id}_{i}.jpg")
            if download_file(img_url, img_path, timeout=30):
                image_paths.append(img_path)
        
        music_url = data.get('music')
        music_path = None
        if music_url:
            music_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")
            download_file(music_url, music_path, timeout=30)
        
        bot_stats['slideshows_downloaded'] += 1
        return {'type': 'slideshow', 'images': image_paths, 'music': music_path}, data
    
    else:
        video_url = data.get('hdplay') or data.get('play') or data.get('wmplay')
        
        if video_url:
            file_size = get_file_size(video_url)
            duration = data.get('duration', 0)
            
            if (file_size and file_size > MAX_VIDEO_SIZE_MB) or duration > 180:
                return {
                    'type': 'link',
                    'url': video_url,
                    'size': file_size,
                    'duration': duration
                }, data
            
            filepath = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")
            if download_file(video_url, filepath, timeout=120):
                actual_size = os.path.getsize(filepath) / (1024 * 1024)
                if actual_size > 50:
                    os.remove(filepath)
                    return {
                        'type': 'link',
                        'url': video_url,
                        'size': actual_size,
                        'duration': duration
                    }, data
                
                bot_stats['videos_downloaded'] += 1
                return {'type': 'video', 'path': filepath}, data
            else:
                return {
                    'type': 'link',
                    'url': video_url,
                    'size': file_size,
                    'duration': duration
                }, data
    
    return None, data


def cleanup_files(files):
    if isinstance(files, list):
        for f in files:
            if f and os.path.exists(f):
                os.remove(f)
    elif files and os.path.exists(files):
        os.remove(files)


def format_info_message(data):
    """تنسيق رسالة المعلومات الكاملة"""
    author = data.get('author', {})
    music = data.get('music_info', {})
    
    create_date = "غير معروف"
    if data.get('create_time'):
        try:
            create_date = datetime.fromtimestamp(data['create_time']).strftime('%Y-%m-%d %H:%M')
        except:
            pass
    
    content_type = "فيديو"
    if data.get('images'):
        content_type = f"صور ({len(data['images'])} صورة)"
    if data.get('is_ad'):
        content_type += " [اعلان]"
    if data.get('is_commercial'):
        content_type += " [تجاري]"
    
    sound_type = "اصلي" if music.get('original') else "مقتبس"
    bio_text = author.get('signature', '')[:100] if author.get('signature') else 'لا يوجد'
    
    return f"""صاحب الفيديو:

الاسم: {author.get('nickname', 'غير معروف')}
المعرف: @{author.get('unique_id', 'غير معروف')}
الايدي: {author.get('id', 'غير معروف')}
البايو: {bio_text}
البلد: {data.get('region', 'غير معروف')}

الفيديو:

النوع: {content_type}
العنوان: {data.get('title', 'بدون عنوان')[:100]}
المدة: {data.get('duration', 0)} ثانية
تاريخ النشر: {create_date}

الاحصائيات:

المشاهدات: {format_number(data.get('play_count', 0))}
الاعجابات: {format_number(data.get('digg_count', 0))}
التعليقات: {format_number(data.get('comment_count', 0))}
المشاركات: {format_number(data.get('share_count', 0))}
التحميلات: {format_number(data.get('download_count', 0))}
المحفوظات: {format_number(data.get('collect_count', 0))}
اعادة النشر: {format_number(data.get('repost_count', 0))}

الصوت:

العنوان: {music.get('title', 'غير معروف')}
الفنان: {music.get('author', 'غير معروف')}
الالبوم: {music.get('album', 'غير معروف')}
المدة: {music.get('duration', 0)} ثانية
النوع: {sound_type}"""


def send_subscription_message(chat_id):
    keyboard = types.InlineKeyboardMarkup()
    btn_subscribe = types.InlineKeyboardButton("اشترك في القناة", url=CHANNEL_LINK)
    btn_check = types.InlineKeyboardButton(" ابدا ", callback_data="check_subscription")
    keyboard.add(btn_subscribe)
    keyboard.add(btn_check)
    
    message_text = """لاستخدام البوت يجب عليك الاشتراك في قناتنا اولا.

1. اضغط على زر "اشترك في القناة"
2. بعد الاشتراك اضغط على "ابدا"
"""
    bot.send_message(chat_id, message_text, reply_markup=keyboard)


def get_stats_message():
    """الحصول على رسالة الاحصائيات"""
    uptime = datetime.now() - bot_stats['start_time']
    days = uptime.days
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    
    return f"""احصائيات البوت:

عدد المستخدمين: {len(bot_stats['total_users'])}
اجمالي التحميلات: {bot_stats['total_downloads']}
فيديوهات: {bot_stats['videos_downloaded']}
صور: {bot_stats['slideshows_downloaded']}
تحميلات فاشلة: {bot_stats['failed_downloads']}

وقت التشغيل: {days} يوم و {hours} ساعة و {minutes} دقيقة
تاريخ التشغيل: {bot_stats['start_time'].strftime('%Y-%m-%d %H:%M')}"""


# امر المساعدة
@bot.message_handler(commands=['info'])
def cmd_help(message):
    help_text = """دليل استخدام البوت:

1. ارسل رابط فيديو تيك توك
2. انتظر حتى يتم التحميل
3. اختر اذا تريد معلومات صاحب الفيديو


ملاحظات:
- الفيديوهات الكبيرة ستحصل على رابط مباشر
- يدعم البوت الفيديوهات والصور

الاوامر:
/dev - معلومات المطور
"""
    bot.reply_to(message, help_text)


# امر المطور
@bot.message_handler(commands=['dev'])
def cmd_dev(message):
    keyboard = types.InlineKeyboardMarkup()
    btn_dev = types.InlineKeyboardButton("تواصل مع المطور", url=f"https://t.me/{DEVELOPER_USERNAME}")
    keyboard.add(btn_dev)
    
    dev_text = f"""معلومات المطور:

telegram: @{DEVELOPER_USERNAME}
tiktok: @f60r
snapchat: @dmg.309

للاقتراحات او الشكاوى تواصل مع المطور.
"""
    bot.reply_to(message, dev_text, reply_markup=keyboard)


# امر ارسال الاحصائيات للمطور
@bot.message_handler(commands=['send'])
def cmd_send(message):
    if not is_developer(message):
        bot.reply_to(message, "هذا الامر للمطور فقط.")
        return
    
    stats_message = get_stats_message()
    bot.reply_to(message, stats_message)


# امر الاحصائيات
@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    if not is_developer(message):
        bot.reply_to(message, "هذا الامر للمطور فقط.")
        return
    
    stats_message = get_stats_message()
    bot.reply_to(message, stats_message)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.strip().lower()
    original_text = message.text.strip()
    user_name = message.from_user.first_name or "صديقي"
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # اضافة المستخدم للاحصائيات
    bot_stats['total_users'].add(user_id)
    
    if text == 'start' or text == '/start':
        if not check_subscription(user_id):
            send_subscription_message(chat_id)
            return

        bot.reply_to(
            message,
            f"""اهلا وسهلا {user_name}! 👋

        /info - للمعلومات

        """
            )
        return
    
    if re.search(r'(tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com)', text, re.IGNORECASE):
        
        if not check_subscription(user_id):
            send_subscription_message(chat_id)
            return
        
        msg = bot.reply_to(message, "جاري التحميل... انتظر قليلا")
        
        try:
            result, data = process_video(original_text)
            
            if not result:
                bot.edit_message_text("فشل التحميل. جرب مرة اخرى بعد قليل.", chat_id, msg.message_id)
                bot_stats['failed_downloads'] += 1
                return
            
            bot_stats['total_downloads'] += 1
            
            if data:
                video_info_cache[chat_id] = data
            
            bot.delete_message(chat_id, msg.message_id)
            
            if result['type'] == 'video':
                filepath = result['path']
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as video_file:
                        bot.send_video(chat_id, video_file, caption="تم التحميل!")
                    cleanup_files(filepath)
            
            elif result['type'] == 'link':
                size_text = f"{result['size']:.1f} MB" if result['size'] else "غير معروف"
                duration_text = format_duration(result['duration']) if result['duration'] else "غير معروف"
                
                keyboard = types.InlineKeyboardMarkup()
                btn_download = types.InlineKeyboardButton("تحميل الفيديو", url=result['url'])
                keyboard.add(btn_download)
                
                link_message = f"""الفيديو كبير الحجم!

الحجم: {size_text}
المدة: {duration_text}

اضغط الزر للتحميل المباشر:"""
                
                bot.send_message(chat_id, link_message, reply_markup=keyboard)
                    
            elif result['type'] == 'slideshow':
                images = result['images']
                music = result.get('music')
                
                if images:
                    for i in range(0, len(images), 10):
                        batch = images[i:i+10]
                        media_group = []
                        for img_path in batch:
                            if os.path.exists(img_path):
                                with open(img_path, 'rb') as img_file:
                                    media_group.append(types.InputMediaPhoto(img_file.read()))
                        if media_group:
                            bot.send_media_group(chat_id, media_group)
                
                if music and os.path.exists(music):
                    with open(music, 'rb') as audio_file:
                        bot.send_audio(chat_id, audio_file, caption="الصوت")
                
                cleanup_files(images)
                cleanup_files(music)
            
            if data:
                keyboard = types.InlineKeyboardMarkup()
                btn_yes = types.InlineKeyboardButton("نعم", callback_data="show_info")
                btn_no = types.InlineKeyboardButton("لا", callback_data="no_info")
                keyboard.add(btn_yes, btn_no)
                bot.send_message(chat_id, "هل تريد معلومات صاحب الفيديو؟", reply_markup=keyboard)
                
        except Exception as e:
            bot.reply_to(message, f"حصل خطأ: {str(e)[:200]}")
            bot_stats['failed_downloads'] += 1
            print(f"خطأ: {e}")
    else:
        if not check_subscription(user_id):
            send_subscription_message(chat_id)
            return
        bot.reply_to(message, f"{user_name}، ارسل رابط تيك توك صحيح")


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    user_name = call.from_user.first_name or "صديقي"
    
    # اضافة المستخدم للاحصائيات
    bot_stats['total_users'].add(user_id)
    
    if call.data == "check_subscription":
        if check_subscription(user_id):
            bot.delete_message(chat_id, call.message.message_id)
            bot.send_message(chat_id, f"اهلا {user_name}! تم التحقق من اشتراكك.\n\nارسل رابط التيك توك للتحميل.")
        else:
            bot.answer_callback_query(call.id, f"{user_name} علينا..؟ اشترك وتعال ^_^", show_alert=True)
    
    elif call.data == "show_info":
        data = video_info_cache.get(chat_id)
        
        if data:
            info_message = format_info_message(data)
            author = data.get('author', {})
            avatar = author.get('avatar_larger') or author.get('avatar')
            
            keyboard = types.InlineKeyboardMarkup()
            profile_url = f"https://www.tiktok.com/@{author.get('unique_id', '')}"
            btn_profile = types.InlineKeyboardButton("زيارة الحساب", url=profile_url)
            keyboard.add(btn_profile)
            
            if avatar:
                try:
                    bot.send_photo(chat_id, avatar, caption=info_message, reply_markup=keyboard)
                except:
                    bot.send_message(chat_id, info_message, reply_markup=keyboard)
            else:
                bot.send_message(chat_id, info_message, reply_markup=keyboard)
            
            del video_info_cache[chat_id]
        else:
            bot.send_message(chat_id, "عذرا، انتهت صلاحية المعلومات.")
        
        bot.delete_message(chat_id, call.message.message_id)
        
    elif call.data == "no_info":
        if chat_id in video_info_cache:
            del video_info_cache[chat_id]
        bot.delete_message(chat_id, call.message.message_id)
        bot.send_message(chat_id, f"حسنآ  {user_name} ، ارسل رابط اخر متى ما اردت")


print("البوت شغال...")
bot.infinity_polling()
