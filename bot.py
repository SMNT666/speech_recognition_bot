import os
import telebot
import soundfile as sf
import speech_recognition as speech_r
import asyncio
from datetime import datetime, time
import moviepy.editor as mp
import json

try:
    with open('config.json', 'r') as config_file:
        config_data = json.load(config_file)

    api_key = config_data.get('api_key')
except FileNotFoundError:
    print("Файл конфигурации не найден.")
except json.JSONDecodeError:
    print("Ошибка при чтении файла конфигурации JSON.")

TOKEN = api_key
bot = telebot.TeleBot(TOKEN)


async def process_video_note_message(message):
    try:
        file_info = bot.get_file(message.video_note.file_id)
        file_path = file_info.file_path

        # Загружаем видео-сообщение
        downloaded_file = bot.download_file(file_path)

        # Генерируем уникальное имя файла на основе времени
        current_time = datetime.now().strftime('%Y%m%d%H%M%S')
        video_file_path = f'video_note_{current_time}.mp4'

        with open(video_file_path, 'wb') as video_file:
            video_file.write(downloaded_file)

        # Извлекаем аудио из видео
        audio_file_path = f'audio_{current_time}.wav'
        video_clip = mp.VideoFileClip(video_file_path)
        audio_clip = video_clip.audio
        audio_clip.write_audiofile(audio_file_path)

        # Закрываем объекты video_clip и audio_clip
        audio_clip.close()
        video_clip.close()

        # Распознавание аудио
        r = speech_r.Recognizer()

        with speech_r.AudioFile(audio_file_path) as source:
            audio = r.record(source)
            r.adjust_for_ambient_noise(source)
            text_result = r.recognize_google(audio, language="ru-RU", show_all=True)
            recognized_text = text_result.get('alternative', [{}])[0].get('transcript', '')

        print("Recognized text:", recognized_text)

        # Отправляем текстовую версию в чат
        bot.reply_to(message, recognized_text)

        # Удаляем временные файлы
        os.remove(video_file_path)
        os.remove(audio_file_path)

    except Exception as e:
        print(e)
        bot.reply_to(message, "Произошла ошибка при обработке видео-сообщения.")


async def process_voice_message(message):
    try:
        file_info = bot.get_file(message.voice.file_id)
        file_path = file_info.file_path

        # Загружаем голосовое сообщение
        downloaded_file = bot.download_file(file_path)

        # Генерируем уникальное имя файла на основе времени
        current_time = datetime.now().strftime('%Y%m%d%H%M%S')
        audio_file_path = f'audio_{current_time}.ogg'

        with open(audio_file_path, 'wb') as audio_file:
            audio_file.write(downloaded_file)

        # Конвертируем OGG в WAV
        ogg_audio, sample_rate = sf.read(audio_file_path)
        wav_file_path = f'audio_{current_time}.wav'
        sf.write(wav_file_path, ogg_audio, sample_rate)

        # Распознавание аудио
        r = speech_r.Recognizer()

        with speech_r.AudioFile(wav_file_path) as source:
            audio = r.record(source)
            r.adjust_for_ambient_noise(source)
            text_result = r.recognize_google(audio, language="ru-RU", show_all=True)
            recognized_text = text_result.get('alternative', [{}])[0].get('transcript', '')

        print("Recognized text:", recognized_text)

        # Отправляем текстовую версию в чат
        bot.reply_to(message, recognized_text)

        # Удаляем временные файлы
        os.remove(audio_file_path)
        os.remove(wav_file_path)

    except Exception as e:
        print(e)
        bot.reply_to(message, "Произошла ошибка при обработке аудио.")


@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    asyncio.run(process_voice_message(message))


@bot.message_handler(content_types=['video_note'])
def handle_video_note(message):
    asyncio.run(process_video_note_message(message))


while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
        time.sleep(15)
