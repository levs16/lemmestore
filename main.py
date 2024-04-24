##################################################################################################
# Bot written by: levs16(bot-side + bug fixing), yes(file management(backend) + Q.Q. + advising) #
# First written on: 06:21 PM 04/18/2024, last edited on: 1:13 AM 04/25/2024                     #
#                                                                                                #
# -Fully open-source-                                                                            # 
##| CC: levs16, yes |#############################################################################  


import telebot
from telebot import types
import os
import json
from collections import defaultdict

TOKEN = 'token-here'
bot = telebot.TeleBot(TOKEN)

# Ensure the directory for storing files exists
if not os.path.exists("user_files"):
    os.makedirs("user_files")


def get_user_storage_info(user_id):
    user_folder = f"user_files/{user_id}"
    total_size = 0
    file_count = 0
    for dirpath, dirnames, filenames in os.walk(user_folder):
        for f in filenames:
            if not f.startswith(".metadata"):  # Exclude metadata files from the count and size calculation
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
                file_count += 1
    return total_size, file_count

def save_file(file_id, user_id, file_name):
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    user_folder = f"user_files/{user_id}"
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    file_path = os.path.join(user_folder, file_name)
    with open(file_path, 'wb') as new_file:
        new_file.write(downloaded_file)
    
    print(f"File {file_name} saved successfully.")

def generate_tree(root_dir):
    tree = defaultdict(dict)

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Get the depth of the current directory, relative to the root_dir
        depth = dirpath[len(root_dir):].count(os.sep)
        # Initialize a reference to the part of the tree we're currently filling
        subtree = tree
        # Dive into the tree to get to the current level
        for _ in range(depth):
            subdir = os.path.basename(dirpath)
            subtree = subtree[subdir]
        # Add directories and files to the current level
        for dirname in dirnames:
            subtree[dirname] = {}
        for filename in filenames:
            if not(filename.startswith(".")):  # Exclude files starting with "." from the tree
                subtree[filename] = None

    return tree

def format_tree(tree, indent=0):
    """Recursively yields lines representing the tree structure."""
    for name, subtree in tree.items():
        yield "    " * indent + name
        if subtree is not None:  # A dict indicates a subtree
            yield from format_tree(subtree, indent + 1)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_message = (
        "🌟 Welcome to the File Manager Bot! 🌟\n\n"
        "I'm here to help you manage your files efficiently. Here's what you can do:\n"
        "- 📤 Upload files with /upload\n"
        "- 📂 View your files with /files\n"
        "- 📥 Download files with /download\n"
        "- 🏷️ Tag your files for easy organization with /tag\n"
        "- 🎛️ Access the main panel anytime with /panel\n\n"
        "💡 Start by uploading some files or viewing your existing files. If you need help, just type /help.\n\n"
        "Remember, you have a 10GB storage limit. Manage your files wisely! 💾"
    )
    bot.reply_to(message, welcome_message)

@bot.message_handler(commands=['upload'])
def upload_file(message):
    bot.reply_to(message, "Please send the file you want to upload.")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    file_info = message.document
    file_id = file_info.file_id
    file_name = file_info.file_name
    user_id = message.from_user.id

    # Save the file
    save_file(file_id, user_id, file_name)

    bot.reply_to(message, f"File {file_name} has been uploaded successfully.")

def list_user_files(user_id):
    user_folder = f"user_files/{user_id}"
    if os.path.exists(user_folder):
        files = os.listdir(user_folder)
        files = [f for f in files if not f.startswith(".metadata")]
        if files:
            return "Your files:\n" + "\n".join(files)
        else:
            return "You have no files."
    else:
        return "You have no files."

@bot.message_handler(commands=['files'])
def list_files(message):
    user_id = message.from_user.id
    response = list_user_files(user_id)
    bot.reply_to(message, response)

def list_downloadable_files(user_id, chat_id):
    user_folder = f"user_files/{user_id}"
    if os.path.exists(user_folder):
        files = os.listdir(user_folder)
        files = [f for f in files if not f.startswith(".metadata")]
        if files:
            markup = types.InlineKeyboardMarkup()
            for file in files:
                markup.add(types.InlineKeyboardButton(file, callback_data=f"download_{file}"))
            bot.send_message(chat_id, "Choose the file to download:", reply_markup=markup)
        else:
            bot.send_message(chat_id, "You have no files. 🚫")
    else:
        bot.send_message(chat_id, "You have no files. 🚫")

@bot.message_handler(commands=['download'])
def download_file(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    list_downloadable_files(user_id, chat_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("download_"))
def callback_query(call):
    file_name = call.data[len("download_"):]
    if file_name.startswith(".metadata"):
        bot.answer_callback_query(call.id, "This file is not accessible. 🚫")
        return
    user_folder = f"user_files/{call.from_user.id}"
    file_path = os.path.join(user_folder, file_name)
    if os.path.exists(file_path) and not file_name.startswith(".metadata"):
        with open(file_path, 'rb') as file:
            bot.send_document(call.message.chat.id, file)
        bot.answer_callback_query(call.id, "Downloading file... 📥")
    else:
        bot.answer_callback_query(call.id, "File not found. 🚫")

@bot.message_handler(commands=['panel'])
def main_panel(message):
    user_id = message.from_user.id
    total_size, file_count = get_user_storage_info(user_id)
    used_storage_gb = total_size / (1024**3)  # Convert bytes to gigabytes

    if file_count == 0:
        bot.reply_to(message, "You have no files.")
        return

    panel_summary = (
        f"Welcome to your control panel! Here's a summary of your usage:\n\n"
        f"📂 Files stored: {file_count}\n"
        f"📦 Storage used: {used_storage_gb:.2f} GB / 10 GB\n\n"
        "Commands:\n"
        "/start - Get started with the bot 🚀\n"
        "/upload - Upload new files 📤\n"
        "/files - View your uploaded files 📂\n"
        "/download - Download your files 📥\n"
        "/tag - Add tags to your files 🏷️\n"
        "/help - Get help with commands ❓\n\n"
        "Manage your files wisely! 💾"
    )
    markup = types.InlineKeyboardMarkup()
    commands = [("/start", "Start 🚀"), ("/upload", "Upload 📤"), ("/files", "Files 📂"), ("/download", "Download 📥"), ("/tag", "Tag 🏷️"), ("/help", "Help ❓")]
    for command, description in commands:
        markup.add(types.InlineKeyboardButton(description, callback_data="panel_" + command.replace("/", "")))
    bot.send_message(message.chat.id, panel_summary, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("inittag_"))
def file_to_tag_selected(call):
    file_name = call.data[len("inittag_"):]

    if file_name.startswith(".metadata"):
        bot.send_message(call.message.chat.id, "This file cannot be tagged. 🚫")
        return

    msg = f"You selected {file_name}. Please enter the tags now (use spaces to separate multiple tags):"
    bot.send_message(call.message.chat.id, msg)

    # Wait for the user to enter tags and then process them
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, tag_input_received, file_name, call.from_user.id)

@bot.callback_query_handler(func=lambda call: True)
def handle_command(call):
    bot.answer_callback_query(call.id)
    command = call.data.replace("panel_", "")
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    print(command)

    if command == "start":
        send_welcome(call.message)
    elif command == "upload":
        upload_file(call.message)
    elif command == "files":
        response = list_user_files(user_id)
        bot.send_message(chat_id, response)
    elif command == "download":
        list_downloadable_files(user_id, chat_id)
    elif command.startswith("tag"):
        list_taggable_files(user_id, chat_id)
    elif command == "help":
        send_help(call.message)
    else:
        bot.send_message(call.message.chat.id, "Unknown command. Please try again.")

def list_taggable_files(user_id, chat_id):
    user_folder = f"user_files/{user_id}"
    if os.path.exists(user_folder):
        files = os.listdir(user_folder)
        files = [f for f in files if not f.startswith(".metadata")]
        if files:
            markup = types.InlineKeyboardMarkup()
            for file_name in files:
                markup.add(types.InlineKeyboardButton(file_name, callback_data=f"inittag_{file_name}"))
            bot.send_message(chat_id, "Select the file you want to tag:", reply_markup=markup)
        else:
            bot.send_message(chat_id, "You have no files to tag. 🚫")
    else:
        bot.send_message(chat_id, "You have no files to tag. 🚫")

@bot.message_handler(commands=['tag'])
def tag_file_init(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    list_taggable_files(user_id, chat_id)

def tag_input_received(message, file_name, user_id):
    tags = message.text.split()  # Assuming tags are space-separated
    user_folder = f"user_files/{user_id}"
    metadata_path = os.path.join(user_folder, ".metadata.json")

    # Check if the metadata file exists, if not, create an empty one
    if not os.path.exists(metadata_path):
        with open(metadata_path, 'w') as f:
            json.dump({}, f)  # Create an empty JSON dictionary

    # Now open the metadata file to update it
    with open(metadata_path, 'r+') as f:
        metadata = json.load(f)
        metadata[file_name] = {"tags": tags}  # Add or update the file's tags
        f.seek(0)  # Move to the start of the file before writing
        json.dump(metadata, f)
        f.truncate()  # Truncate file to remove any leftover data

    bot.reply_to(message, f"Tags {', '.join(tags)} have been added to {file_name}. 🏷️")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "/start - Welcome message 🚀\n"
        "/upload - Upload a file 📤\n"
        "/files - List your files 📂\n"
        "/download - Download a file 📥\n"
        "/tag - Tag a file 🏷️\n"
        "/panel - Access the main panel 🎛️\n"
        "Remember, you have a 10GB limit for your files. 💾"
    )
    bot.reply_to(message, help_text)

bot.infinity_polling()
