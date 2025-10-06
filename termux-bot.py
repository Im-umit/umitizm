#!/data/data/com.termux/files/usr/bin/python3
import subprocess
import os
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

print("TERMUX TELEGRAM BOT KURULUMU")
print("=" * 40)

# Kullanıcıdan bilgileri al
def setup_bot():
    print("\nLutfen asagidaki bilgileri girin:")
    
    # Bot Token
    token = input("Bot Token'inizi girin: ").strip()
    if not token:
        print("HATA: Bot Token gerekli!")
        sys.exit(1)
    
    # Telegram ID
    user_id = input("Telegram ID'nizi girin: ").strip()
    if not user_id.isdigit():
        print("HATA: Gecerli bir Telegram ID girin!")
        sys.exit(1)
    
    return token, int(user_id)

# Bilgileri al
TOKEN, AUTHORIZED_USERS = setup_bot()

print(f"\nBot ayarlari tamamlandi!")
print(f"Yetkili kullanici: {AUTHORIZED_USERS}")
print("Bot baslatiliyor...\n")

def auth_required(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in AUTHORIZED_USERS:
            await update.message.reply_text("Bu botu kullanma yetkiniz yok!")
            return
        return await func(update, context)
    return wrapper

@auth_required
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Merhaba {user.first_name}!\n\n"
        "Termux Bot aktif!\n\n"
        "Kullanilabilir Komutlar:\n"
        "/start - Botu baslat\n"
        "/sysinfo - Sistem bilgisi\n"
        "/files - Dosya listesi\n"
        "/battery - Pil durumu\n"
        "/python <kod> - Python kodu calistir\n"
        "/install <paket> - Paket kur\n"
        "/update - Sistemi guncelle\n\n"
        "Not: Direkt komut da yazabilirsiniz (ls, pwd, neofetch vb.)"
    )

@auth_required
async def execute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.message.text.strip()
    
    if not command:
        await update.message.reply_text("Bos komut gonderilemez!")
        return
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        
        output = ""
        if result.stdout:
            output += f"Cikti:\n{result.stdout}\n"
        if result.stderr:
            output += f"Hata:\n{result.stderr}\n"
        if not output:
            output = "Komut basariyla calisti."
        
        if len(output) > 4000:
            output = output[:4000] + "\n... (devami var)"
            
        await update.message.reply_text(output)
        
    except subprocess.TimeoutExpired:
        await update.message.reply_text("Komut zaman asimina ugradi (30 saniye)")
    except Exception as e:
        await update.message.reply_text(f"Hata: {str(e)}")

@auth_required
async def sysinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        info = "Sistem Bilgisi:\n\n"
        commands = {
            "Sistem": "uname -a",
            "Bellek": "free -h",
            "Disk": "df -h",
            "Pil": "termux-battery-status"
        }
        
        for key, cmd in commands.items():
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                if result.stdout:
                    info += f"{key}: {result.stdout.strip()}\n\n"
            except:
                info += f"{key}: Bilgi alinamadi\n\n"
        
        await update.message.reply_text(info)
    except Exception as e:
        await update.message.reply_text(f"Hata: {e}")

@auth_required
async def files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = subprocess.run("ls -la", shell=True, capture_output=True, text=True)
        await update.message.reply_text(f"Dosyalar:\n{result.stdout}")
    except Exception as e:
        await update.message.reply_text(f"Hata: {e}")

@auth_required
async def battery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = subprocess.run("termux-battery-status", shell=True, capture_output=True, text=True)
        await update.message.reply_text(f"Pil Durumu:\n{result.stdout}")
    except:
        await update.message.reply_text("Pil bilgisi alinamadi.")

@auth_required
async def python_run(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        code = " ".join(context.args)
        try:
            result = subprocess.run(f"python -c '{code}'", shell=True, capture_output=True, text=True)
            output = result.stdout or result.stderr or "Kod basariyla calisti."
            await update.message.reply_text(f"Python Ciktisi:\n{output}")
        except Exception as e:
            await update.message.reply_text(f"Hata: {e}")
    else:
        await update.message.reply_text("Kullanim: /python <python_kodu>")

@auth_required
async def install(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        pkg = context.args[0]
        await update.message.reply_text(f"{pkg} kuruluyor...")
        result = subprocess.run(f"pkg install -y {pkg}", shell=True, capture_output=True, text=True)
        output = result.stdout or result.stderr or "Kurulum tamamlandi."
        await update.message.reply_text(f"Kurulum Sonucu:\n{output}")
    else:
        await update.message.reply_text("Kullanim: /install <paket_adi>")

@auth_required
async def update_system(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sistem guncelleniyor...")
    result = subprocess.run("pkg update && pkg upgrade -y", shell=True, capture_output=True, text=True)
    await update.message.reply_text("Sistem guncellemesi tamamlandi!")

@auth_required
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

def main():
    try:
        app = Application.builder().token(TOKEN).build()
        
        commands = [
            ("start", start),
            ("sysinfo", sysinfo),
            ("files", files),
            ("battery", battery),
            ("python", python_run),
            ("install", install),
            ("update", update_system),
            ("help", help_cmd),
        ]
        
        for cmd, handler in commands:
            app.add_handler(CommandHandler(cmd, handler))
        
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, execute_command))
        
        print("Bot baslatildi!")
        print("Telegram'dan botunuza /start yazin")
        print("Durdurmak icin: CTRL + C\n")
        
        app.run_polling()
        
    except Exception as e:
        print(f"Bot baslatilamadi: {e}")
        print("Hata cozumu:")
        print("   - Bot token'ini kontrol edin")
        print("   - Internet baglantinizi kontrol edin")
        print("   - python-telegram-bot kutuphanesi kurulu mu?")

if __name__ == "__main__":
    main()
