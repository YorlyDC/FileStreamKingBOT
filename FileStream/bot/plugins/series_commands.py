import logging
from FileStream.bot import FileStream
from FileStream.utils.bot_utils import is_user_authorized
from FileStream.utils.database import Database
from FileStream.utils.series_handler import SeriesHandler
from FileStream.config import Telegram, Server
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums.parse_mode import ParseMode

db = Database(Telegram.DATABASE_URL, Telegram.SESSION_NAME)
series_handler = SeriesHandler()

@FileStream.on_message(filters.command("start_series") & filters.private)
async def start_series_cmd(_, message: Message):
    """Iniciar modo serie - Uso: /start_series <título de la serie>"""
    if not await is_user_authorized(message):
        return

    # Verificar si ya está en modo serie
    if await db.is_in_series_mode(message.from_user.id):
        current_series = await db.get_current_series(message.from_user.id)
        await message.reply_text(
            f"❌ Ya estás en modo serie con '{current_series}'\n"
            "Usa /finish_series para finalizar la serie actual antes de empezar otra",
            parse_mode=ParseMode.HTML
        )
        return

    # Obtener el título de la serie
    if len(message.command) < 2:
        await message.reply_text(
            "❌ Por favor proporciona el título de la serie\n"
            "Uso: /start_series <título de la serie>",
            parse_mode=ParseMode.HTML
        )
        return

    series_title = " ".join(message.command[1:])
    
    # Iniciar modo serie
    await db.start_series_mode(message.from_user.id, series_title)
    series_handler.start_series(series_title)
    
    await message.reply_text(
        f"✅ Modo serie iniciado para '{series_title}'\n\n"
        "Ahora puedes enviar los episodios. El nombre de cada archivo debe incluir "
        "el número de temporada y episodio en alguno de estos formatos:\n"
        "- S01E02\n"
        "- 1x02\n"
        "- Temporada 1 Episodio 2\n\n"
        "Cuando termines, usa /finish_series para generar los links",
        parse_mode=ParseMode.HTML
    )

@FileStream.on_message(filters.command("finish_series") & filters.private)
async def finish_series_cmd(_, message: Message):
    """Finalizar modo serie y generar links"""
    if not await is_user_authorized(message):
        return

    # Verificar si está en modo serie
    if not await db.is_in_series_mode(message.from_user.id):
        await message.reply_text(
            "❌ No estás en modo serie\n"
            "Usa /start_series para iniciar una serie",
            parse_mode=ParseMode.HTML
        )
        return

    try:
        # Obtener archivos de la serie
        series_files = await db.get_series_files(message.from_user.id)
        series_title = await db.get_current_series(message.from_user.id)

        if not series_files:
            await message.reply_text(
                "❌ No hay archivos en la serie actual",
                parse_mode=ParseMode.HTML
            )
            return

        # Procesar cada archivo
        for file in series_files:
            file_info = file['info']
            file_id = file['file_id']
            
            # Generar links
            page_link = f"{Server.URL}watch/{file_id}"
            stream_link = f"{Server.URL}dl/{file_id}"
            
            # Agregar a series_handler
            series_handler.add_file(file_info, stream_link, page_link)

        # Generar archivos de salida
        json_data = series_handler.export_to_json()
        txt_data = series_handler.export_to_txt()

        # Enviar archivos
        await message.reply_document(
            document=json_data.encode(),
            file_name=f"{series_title}.json",
            caption="📄 Información de la serie en formato JSON",
            parse_mode=ParseMode.HTML
        )

        await message.reply_document(
            document=txt_data.encode(),
            file_name=f"{series_title}.txt",
            caption="📄 Links de la serie organizados por temporada",
            parse_mode=ParseMode.HTML
        )

        # Limpiar estado
        await db.end_series_mode(message.from_user.id)
        series_handler.clear()

        await message.reply_text(
            "✅ Serie finalizada exitosamente",
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        logging.error(f"Error processing series: {e}")
        await message.reply_text(
            "❌ Ocurrió un error al procesar la serie\n"
            "Por favor intenta nuevamente",
            parse_mode=ParseMode.HTML
        )
        # Limpiar estado en caso de error
        await db.end_series_mode(message.from_user.id)
        series_handler.clear() 