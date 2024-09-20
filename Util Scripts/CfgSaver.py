import json
import os
# Функция для сохранения настроек в JSON файл
def save_config(filename, config):
    with open(filename, 'w') as file:
        json.dump(config, file, indent=4)


# Пример сохранения новых настроек
new_config = dict(
    AiServer_enable = True,
    WebServer_enable = True,
    TgBot_enable = False,
    INPUT_FOLDER = "input_audio",
    OUTPUT_FOLDER = "output_audio",
    #ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg'},
    OpenAiToken = "sk-bP0zkdB03jPrmXavHzd6R0ZLqmhlnibi",
    TemplateFolder="Page"
)
save_config('../config.json', new_config)