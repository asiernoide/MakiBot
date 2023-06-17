import asyncio
import os
import random
from typing import Union
import discohook
import requests
import pymongo

# Variables de entorno

APPLICATION_ID = os.environ.get('APPLICATION_ID')
APPLICATION_TOKEN = os.environ.get('APPLICATION_TOKEN')
APPLICATION_PUBLIC_KEY = os.environ.get('APPLICATION_PUBLIC_KEY')

# Opcional (pero recomendable)
MONGODB_URI = os.environ.get('MONGODB_URI')
MONGODB_NAME = os.environ.get('MONGODB_DBNAME')

# Datasets
MEDIA_CHOICES = [
    discohook.Choice("Todas", "all"),
    discohook.Choice("Danganronpa", "danganronpa_characters"),
    discohook.Choice("One Piece", "onepiece_characters"),
    discohook.Choice("Zero Escape", "zeroescape_characters"),
    discohook.Choice("JoJo's Bizarre Adventure", "jojo_characters"),
    discohook.Choice("Overwatch", "overwatch_characters"),
    discohook.Choice("Dark Souls", "darksouls_characters"),
    discohook.Choice("My Little Pony", "mlp_characters")
]

# Comandos

COMMAND_HELP = {
    "Utilidades": [
        {
            "name": "/help",
            "description": "Muestra este mensaje de ayuda."
        },
        {
            "name": "/invite `[duración]`",
            "description": "Envía una invitación a este servidor. Puedes especificar una duración para la invitación (en días). Si eliges \"0\", la invitación no caducará. **Se necesitan permisos para crear invitaciones para usar este comando.**"
        },
        {
            "name": "/vote `enunciado` `opcion_1` `[opcion_2]` `[opcion_3]` `[opcion_4]`",
            "description": "Crea una votación con hasta 4 opciones."
        },
        {
            "name": "/roll `caras`",
            "description": "Tira un dado de `n` caras."
        },
        {
            "name": "/coinflip",
            "description": "Tira una moneda."
        }
    ],
    "Entretenimiento": [
        {
            "name": "/meme",
            "description": "Envía un meme aleatorio."
        },
        {
            "name": "/waifu `obra`",
            "description": "¿Cuál es tu waifu/husbando? Elige un personaje aleatorio de una obra a tu elección (o de todas)."
        },
        {
            "name": "/neverhaveiever `[categoría]`",
            "description": "Juega un Yo Nunca (solo disponible en inglés). Puedes especificar una categoría. Si no se especifica, se escogen preguntas de entre todas."
        },
        {
            "name": "/kissmarrykill `obra`",
            "description": "Juega a Kiss/Marry/Kill con personajes aleatorios de una obra a tu elección (o de todas)."
        },
        {
            "name": "/scp",
            "description": "Envía un SCP aleatorio (**ADVERTENCIA: Este comando no funciona correctamente el 100% de las veces**)."
        },
        {
            "name": "/8ball `pregunta`",
            "description": "Pregunta a la bola mágica."
        }
    ],
    "NSFW": [
        {
            "name": "/shitpost",
            "description": "Envía un copypasta aleatorio."
        }
    ]
}

# Inicializar variable para BD (para poder usarla en el resto del código)
db = None

# Establecer la conexión con la base de datos (solo si las variables no están vacías)
if MONGODB_URI and MONGODB_NAME:
    client = pymongo.MongoClient(MONGODB_URI)
    db = client[MONGODB_NAME]
    print("Conexión con la base de datos establecida.")
else:
    print("No se estableció la conexión con la base de datos.")


app = discohook.Client(
    application_id=APPLICATION_ID,
    token=APPLICATION_TOKEN,
    public_key=APPLICATION_PUBLIC_KEY
)

# Private functions


def _get_random_characters(char_collection: str, num: int = 1, gender: Union[str, None] = None):
    '''Obtiene una lista de "num" personajes aleatorios de cualquier colección de la base de datos
    O el personaje obtenido si "num" es 1.
    Parámetros:
        char_collection: Nombre de la colección de la base de datos.
        num: Número de personajes a obtener.
        gender: Género de los personajes a obtener ("Male" o "Female").
    '''

    # Define la lista de operaciones de agregación
    pipeline = [{"$sample": {"size": num}}]

    if gender is not None:
        pipeline.insert(0, {"$match": {"gender": gender}})

    # Inicializar colección
    if char_collection != "all":
        collection = db[char_collection]
    else:
        # Filter to pick only collections that end with "characters"
        filter = {"name": {"$regex": r".*characters$"}}
        collection_list = db.list_collection_names(filter=filter)
        collection = db[collection_list[0]]
        for c in collection_list:
            if c != collection.name:
                pipeline.insert(0, {'$unionWith': {'coll': f'{c}'}})

    # Ejecuta la consulta de agregación y obtiene el personaje aleatorio
    random_characters = collection.aggregate(pipeline)

    # Inicializar lista de personajes
    character_list = []

    # Obtener los elementos del objeto CommandCursor
    for character in random_characters:
        character_list.append(character)

    # Imprimir el documento
    if len(character_list) == 1:
        return character_list[0]
    else:
        return character_list


global_nhie_id = None


def _update_global_nhie_id(nhie_id):
    global global_nhie_id
    global_nhie_id = nhie_id


def _get_never_have_i_ever(category: Union[str, None] = None):
    nhie_id = global_nhie_id

    # Set up nhie.io API endpoint and parameters
    api_url = "https://api.nhie.io/v2/statements/next"
    params = {}

    if category is not None:
        params["category"] = category

    if nhie_id is not None:
        params["statement_id"] = nhie_id

    # Send API request and parse response
    response = requests.get(api_url, params=params)
    data = response.json()
    question = data["statement"]
    category_used = data["category"]

    # Update global nhie_id
    _update_global_nhie_id(data["ID"])

    return question, category_used

# Public functions

# help command


@app.command(
    name="help",
    description="Comando de ayuda para obtener información sobre los comandos disponibles."
)
async def help_command(interaction: discohook.Interaction):
    cat_embed_list = []

    for cat in COMMAND_HELP.keys():
        commands_info = ""
        for cmd in COMMAND_HELP[cat]:
            commands_info += f"**\"{cmd['name']}\"**\n{cmd['description']}\n\n"
        cat_embed_list.append(discohook.Embed(
            title=cat, description=commands_info, color=0x943b36))

    more_info_embed = discohook.Embed(
        title="Podrás encontrar más información sobre los comandos de MakiBot aquí -> https://makibot.netlify.app/",
    )

    cat_embed_list.insert(0, more_info_embed)

    await interaction.response(
        "Aquí tienes la lista de comandos disponibles:",
        embeds=cat_embed_list
    )

# meme command


@app.command(
    name="meme",
    description="Envía un meme aleatorio"
)
async def meme(interaction: discohook.Interaction):
    resp = requests.get('https://meme-api.com/gimme')
    data = resp.json()
    meme_embed = discohook.Embed()
    meme_embed.image(data.get('url'))
    await interaction.response(
        data.get('title'),
        embed=meme_embed
    )

# waifu command

# waifu - Components
global_character_collection = None


def update_global_character_collection(collection_name):
    global global_character_collection
    global_character_collection = collection_name


@discohook.button("Waifu", style=discohook.ButtonStyle.grey, emoji=discohook.PartialEmoji(name=":female_sign:", id="1100748842024054925"))
async def waifu_button(interaction: discohook.ComponentInteraction):
    if interaction.from_originator:
        # Choose embed color based on the media
        embed_color = 0x000000
        if global_character_collection == "onepiece_characters":
            embed_color = 0xc2bb38
        elif global_character_collection == "danganronpa_characters":
            embed_color = 0x452323
        elif global_character_collection == "zeroescape_characters":
            embed_color = 0x0071a6
        elif global_character_collection == "jojo_characters":
            embed_color = 0x9726d4
        elif global_character_collection == "overwatch_characters":
            embed_color = 0xfa9c1e
        elif global_character_collection == "mlp_characters":
            embed_color = 0xfa3cfa

        random_char = _get_random_characters(
            global_character_collection, 1, "Female")
        waifu_embed = discohook.Embed(
            title=random_char['name'],
            color=embed_color
        )
        waifu_embed.image(random_char['image'])
        await interaction.message.edit(
            content="Tu waifu es:",
            embed=waifu_embed,
            view=None
        )
    else:
        await interaction.response(
            "¡No puedes usar este botón!",
            ephemeral=True
        )


@discohook.button("Husbando", style=discohook.ButtonStyle.grey, emoji=discohook.PartialEmoji(name=":male_sign:", id="1100748859803697233"))
async def husbando_button(interaction: discohook.ComponentInteraction):
    if interaction.from_originator:
        # Choose embed color based on the media
        embed_color = 0x000000
        if global_character_collection == "onepiece_characters":
            embed_color = 0xc2bb38
        elif global_character_collection == "danganronpa_characters":
            embed_color = 0x452323
        elif global_character_collection == "zeroescape_characters":
            embed_color = 0x0071a6
        elif global_character_collection == "jojo_characters":
            embed_color = 0x9726d4
        elif global_character_collection == "overwatch_characters":
            embed_color = 0xfa9c1e
        elif global_character_collection == "mlp_characters":
            embed_color = 0xfa3cfa

        random_char = _get_random_characters(
            global_character_collection, 1, "Male")
        husbando_embed = discohook.Embed(
            title=random_char['name'],
            color=embed_color
        )
        husbando_embed.image(random_char['image'])
        await interaction.message.edit(
            content="Tu husbando es:",
            embed=husbando_embed,
            view=None
        )
    else:
        await interaction.response(
            "¡No puedes usar este botón!",
            ephemeral=True
        )


@discohook.button("Okama", style=discohook.ButtonStyle.grey, emoji=discohook.PartialEmoji(name=":bon_chan:", id="1100749715966017546"))
async def okama_button(interaction: discohook.ComponentInteraction):
    if interaction.from_originator:
        random_char = _get_random_characters("onepiece_characters", 1, "Okama")
        okama_embed = discohook.Embed(
            title=random_char['name'],
            color=0xc2bb38
        )
        okama_embed.image(random_char['image'])
        await interaction.message.edit(
            content="Tu husbando(?... waifu(?... ¡OKAMA! es:",
            embed=okama_embed,
            view=None
        )
    else:
        await interaction.response(
            "¡No puedes usar este botón!",
            ephemeral=True
        )

# waifu - Main command


@app.command(
    name="waifu",
    description="¿Cuál es tu waifu/husbando?",
    options=[
        discohook.StringOption(
                name="obra",
                description="¿De qué obra es tu waifu/husbando?",
                choices=MEDIA_CHOICES,
                required=True
        )
    ]
)
async def waifu(interaction: discohook.Interaction, obra: str):
    # Send message with buttons
    update_global_character_collection(obra)
    view = discohook.View()

    # Okama button only for One Piece
    if (obra == "onepiece_characters"):
        view.add_button_row(waifu_button, husbando_button, okama_button)
    else:
        view.add_button_row(waifu_button, husbando_button)

    await interaction.response(
        content="Selecciona una opción",
        view=view
    )

# kissmarrykill command

# kissmarrykill - Components


@discohook.button("Chicos", style=discohook.ButtonStyle.grey, emoji=discohook.PartialEmoji(name=":male_sign:", id="1100748859803697233"))
async def kmk_male_button(interaction: discohook.ComponentInteraction):
    if interaction.from_originator:
        character_list = _get_random_characters(
            global_character_collection, 3, "Male")

        # Create a message with selected characters in three different embeds (image and name)
        # First, create a list of embeds
        embeds = []
        for character in character_list:
            embed = discohook.Embed(title=character['name'])
            embed.image(character['image'])
            embeds.append(embed)

        await interaction.message.edit(
            content="Escoge un personaje para casarte con él, otro para besarlo y otro para matarlo",
            embeds=embeds,
            view=None
        )
    else:
        await interaction.response(
            "¡No puedes usar este botón!",
            ephemeral=True
        )


@discohook.button("Chicas", style=discohook.ButtonStyle.grey, emoji=discohook.PartialEmoji(name=":female_sign:", id="1100748842024054925"))
async def kmk_female_button(interaction: discohook.ComponentInteraction):
    if interaction.from_originator:
        character_list = _get_random_characters(
            global_character_collection, 3, "Female")

        # Create a message with selected characters in three different embeds (image and name)
        # First, create a list of embeds
        embeds = []
        for character in character_list:
            embed = discohook.Embed(title=character['name'])
            embed.image(character['image'])
            embeds.append(embed)

        await interaction.message.edit(
            content="Escoge un personaje para casarte con él, otro para besarlo y otro para matarlo",
            embeds=embeds,
            view=None
        )
    else:
        await interaction.response(
            "¡No puedes usar este botón!",
            ephemeral=True
        )


@discohook.button("Todos", style=discohook.ButtonStyle.grey, emoji=discohook.PartialEmoji(name=":trans_sign:", id="1100832019669340281"))
async def kmk_all_button(interaction: discohook.ComponentInteraction):
    if interaction.from_originator:
        character_list = _get_random_characters(global_character_collection, 3)

        # Create a message with selected characters in three different embeds (image and name)
        # First, create a list of embeds
        embeds = []
        for character in character_list:
            embed = discohook.Embed(title=character['name'])
            embed.image(character['image'])
            embeds.append(embed)

        await interaction.message.edit(
            content="Escoge un personaje para casarte con él, otro para besarlo y otro para matarlo",
            embeds=embeds,
            view=None
        )
    else:
        await interaction.response(
            "¡No puedes usar este botón!",
            ephemeral=True
        )

# kmk - Main command


@app.command(
    name="kissmarrykill",
    description="Kiss/Marry/Kill",
    options=[
        discohook.StringOption(
            name="obra",
            description="¿De qué obra son los personajes?",
            choices=MEDIA_CHOICES,
            required=True
        )
    ]
)
async def kissmarrykill(interaction: discohook.Interaction, obra: str):
    update_global_character_collection(obra)

    # Create a message with buttons
    view = discohook.View()
    view.add_button_row(kmk_male_button, kmk_female_button, kmk_all_button)

    # Then, create a message with the embeds
    await interaction.response(
        content="Selecciona una opción",
        view=view
    )


# Comandos aleatorios

# roll command

@app.command(
    name="roll",
    description="Tira un dado de n caras",
    options=[discohook.IntegerOption(
        name="caras",
        description="El número de caras del dado",
        required=True,
        min_value=3,
        max_value=100
    )]
)
async def roll(interaction: discohook.Interaction, caras: int):
    # Roll the dice
    result = random.randint(1, caras)

    # Initialize embed
    dice_embed = discohook.Embed(
        title=f"El resultado del dado es: **{result}**",
        color=0xffffff
    )
    dice_embed.image("https://i.imgur.com/zxDQA6y.gif")
    dice_embed.add_field(
        name="Dado usado",
        value=f"{caras} caras (d{caras})"
    )

    # Send result
    await interaction.response(
        embed=dice_embed
    )

# coinflip command


@app.command(
    name="coinflip",
    description="Tira una moneda"
)
async def coinflip(interaction: discohook.Interaction):
    # Throw the coin
    result = random.choice(["cara", "cruz"])

    # Initialize embed
    coin_embed = discohook.Embed(
        title=f"Ha salido **{result}**",
        color=0xaba924
    )
    coin_embed.image("https://i.gifer.com/Fw3P.gif")

    # Send result
    await interaction.response(
        embed=coin_embed
    )

# 8ball command


@app.command(
    name="8ball",
    description="Pregunta a la bola mágica",
    options=[discohook.StringOption(
        name="pregunta",
        description="Pregunta a la bola mágica",
        required=True
    )]
)
async def eightball(interaction: discohook.Interaction, pregunta: str):
    # Get answer
    answer = random.choice([
        "Sí",
        "No",
        "Tal vez",
        "No lo sé",
        "No lo creo"]
    )

    # Initialize embed
    eightball_embed = discohook.Embed(
        title=f"**{answer}**"
    )

    # Send result
    await interaction.response(
        content=f"> {pregunta}",
        embed=eightball_embed
    )

# vote command


@app.command(
    name="vote",
    description="Crea una votación",
    options=[
        discohook.StringOption(
            name="enunciado",
            description="El motivo de la votación",
            required=True
        ),
        discohook.StringOption(
            name="opcion_1",
            description="La primera opción",
            required=True
        ),
        discohook.StringOption(
            name="opcion_2",
            description="La segunda opción",
            required=False
        ),
        discohook.StringOption(
            name="opcion_3",
            description="La tercera opción",
            required=False
        ),
        discohook.StringOption(
            name="opcion_4",
            description="La cuarta opción",
            required=False
        )
    ]
)
async def vote(interaction: discohook.Interaction, enunciado: str):
    # Get options
    options = list(filter(None, interaction.data['options'][1:]))

    # Get all values into a list
    options = [option['value'] for option in options]

    formatted_options = [
        f":regional_indicator_{chr(97+i)}: {item}" for i, item in enumerate(options)]

    # Create embed
    vote_embed = discohook.Embed(
        title=f"{enunciado}",
        description="\n\n".join(formatted_options),
        color=0xb51ed4
    )

    vote_embed.footer("Votación creada por " + interaction.author.name,
                      icon_url=interaction.author.avatar.url)

    # Send result
    await interaction.response(
        embed=vote_embed
    )

    # Calling the internal Discord API to add the reaction
    # To find your unicode emoji as Encoded URL use this website: https://www.urlencoder.org/
    # To do this for components use "interaction.message.id" instead of "interaction.original_response_message().id"
    encoded_emoji_letter_list = ["%F0%9F%87%A6",
                                 "%F0%9F%87%A7", "%F0%9F%87%A8", "%F0%9F%87%A9"]
    msg = await interaction.original_response_message()
    msg_id = msg.id

    for i in range(len(options)):
        emoji = encoded_emoji_letter_list[i]
        await interaction.client.http.request(method="PUT", path=f"/channels/{interaction.channel_id}/messages/{msg_id}/reactions/{emoji}/@me", use_auth=True)
        # wait a moment to avoid rate limit
        await asyncio.sleep(0.2)

# neverhaveiever command


@app.command(
    name="neverhaveiever",
    description="Juega un Yo Nunca (solo disponible en Inglés)",
    options=[
        discohook.StringOption(
            name="categoría",
            description="Elige una categoría",
            choices=[
                discohook.Choice(name="Inofensivo", value="harmless"),
                discohook.Choice(name="Delicado", value="delicate"),
                discohook.Choice(name="Picante", value="offensive")
            ]
        )
    ]
)
async def neverhaveiever(interaction: discohook.Interaction, categoría: Union[str, None] = None):
    chosen_category = categoría

    # Get question
    result_tuple = _get_never_have_i_ever(category=chosen_category)
    question = result_tuple[0]
    category_id = result_tuple[1]

    # Normalize category name
    if category_id == "harmless":
        category = "Inofensivo"
    elif category_id == "delicate":
        category = "Delicado"
    elif category_id == "offensive":
        category = "Picante"

    # Initialize embed
    neverhaveiever_embed = discohook.Embed(
        title=f"{question}",
        color=0xff0000
    )
    neverhaveiever_embed.footer(text=f"Categoría: {category}")

    # Send result
    await interaction.response(
        embed=neverhaveiever_embed
    )

# Aqui va el comando /scp. Usar plantilla que tengo en el escritorio.

# scp command

# scp - Main command


@app.command(
    name="scp",
    description="Envía un SCP aleatorio (experimental)"
)
async def scp(interaction: discohook.Interaction):
    # Get random SCP
    collection = db["scp_objects"]
    pipeline = [{"$sample": {"size": 1}}]
    scp = collection.aggregate(pipeline).next()

    # Create embeds
    embed_list = []

    # SCP info embed
    scp_embed = discohook.Embed(
        title=scp['name'],
        description=scp['content']
    )
    embed_list.append(scp_embed)

    # Image embed
    if scp.get('image') != None:
        image_embed = discohook.Embed()
        image_embed.image(scp['image'])
        embed_list.insert(0, image_embed)

    # Create view for button
    view = discohook.View()
    button_link = discohook.Button(
        style=discohook.ButtonStyle.link,
        label="Ver en la wiki",
        url=f"https://scp.fandom.com/es/wiki/{scp['name']}",
        emoji=discohook.PartialEmoji(name=":SCP:", id="1102250695937228901")
    )
    view.add_button_row(button_link)

    # Send result
    await interaction.response(
        embeds=embed_list,
        view=view
    )

# invite command


@app.command(
    name="invite",
    description="Envía un enlace de invitación a este servidor",
    options=[
        discohook.IntegerOption(
            name="duración",
            description="Duración de la invitación (en días), escribe \"0\" para que no caduque",
            max_value=7,
            min_value=0
        )
    ],
    permissions=[
        discohook.Permissions.create_instant_invite
    ]
)
async def invite(interaction: discohook.Interaction, duración: Union[int, None] = None):
    # Check if the bot is talking through a DM
    # Call internal discord API to get Channel object
    channel = await interaction.client.http.request(method="GET", path=f"/channels/{interaction.channel_id}", use_auth=True)
    channel_data = await channel.json()

    is_dm_channel = channel_data['type'] == discohook.ChannelType.dm.value
    is_group_dm_channel = channel_data['type'] == discohook.ChannelType.group_dm.value

    if is_dm_channel or is_group_dm_channel:
        await interaction.response(
            content="Este comando solo puede usarse en servidores.",
            ephemeral=True
        )
        return

    # Get duration
    if duración is None:
        duración = 1

    # Get invite
    params = {
        "max_age": duración*86400,
        "unique": "true"
    }

    invite = await interaction.client.http.request(method="POST", path=f"/channels/{interaction.channel_id}/invites", use_auth=True, json=params)
    invite = await invite.json()

    # Send result
    await interaction.response(
        content=f"https://discord.gg/{invite['code']}"
    )

# NSFW commands

# shitpost command


@app.command(
    name="shitpost",
    description="Envía un shitpost aleatorio"
)
async def shitpost(interaction: discohook.Interaction):
    # Check if NSFW channel
    channel = await interaction.client.http.request(method="GET", path=f"/channels/{interaction.channel_id}", use_auth=True)
    channel_data = await channel.json()

    channel_type = channel_data['type']
    is_dm_channel = channel_type == discohook.ChannelType.dm.value
    is_group_dm_channel = channel_type == discohook.ChannelType.group_dm.value

    if not is_dm_channel and not is_group_dm_channel and channel_data['nsfw'] == False:
        await interaction.response(
            content="Este comando solo puede usarse en canales NSFW.",
            ephemeral=True
        )
        return

    # Get random shitpost
    collection = db["shitposts"]
    pipeline = [{"$sample": {"size": 1}}]
    shitpost = collection.aggregate(pipeline).next()

    # Create embed
    post_embed = discohook.Embed(
        title=shitpost['nombre'],
        description=shitpost['contenido']
    )

    # Send result
    await interaction.response(
        embed=post_embed
    )
