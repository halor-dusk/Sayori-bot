import envar
from keep_alive import keep_alive

import discord
import cohere

import re
import base64

def main() -> None:
    if not discord.opus.is_loaded():
        print("Loading opus...")
        discord.opus.load_opus("libopus.so")

        if discord.opus.is_loaded():
            print("Opus loaded succesfuly")
        else:
            print("Opus didn't loaded succesfuly")

#     print(f"""
# Bot token is: '{envar.BOT_TOKEN}'
# Api key is: '{envar.AI_KEY}'
# """)

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.voice_states = True

    bot = SayoryBot(intents=intents)
    bot.run(envar.BOT_TOKEN)

class SayoryBot(discord.Client):
    async def on_ready(self) -> None:
        self.ai = cohere.ClientV2(envar.AI_KEY)
        # Model settings
        self.model = "command-a-vision-07-2025"

        with open("assets/settings.txt") as sys_prompt:
            self.system_prompt = sys_prompt.read()
        
        self.temperature: float = 1
        self.max_tokens: int = 60
        # Memory size in messages, 2 means 1 user message and 1 bot answer
        self.MEMORY_SIZE: int = 32*2

        # Prompt works like the settings and the memory for the bot
        # also used to send the message to the bot
        self.history: list[dict[str, str]] = [
            {
                "role": "system",
                "content": self.system_prompt
            }
        ]

        print(f"Logged in as: '{self.user}'")

    async def on_message(self, message: discord.Message) -> None:
        # print(f"Raw message from {message.author.name}: '{message.content}'")

        if message.author == self.user:
            return # The bot should not respond to its own messages
        elif await self.check_reply(message):
            message_content = replace_id_with_displayname(message)
            # print(f"Processed message: '{message_content}'", "Thinking...", sep="\n")
            
            lowered_message = message_content.lower()
            if (
                "join in the call" in lowered_message or 
                "get in the call" in lowered_message or 
                "come to the call" in lowered_message or
                "come to the channel" in lowered_message or
                "get in the voice channel" in lowered_message or
                "join in the voice channel" in lowered_message 
            ):
                # print("Joining in the call...")

                if not message.author.voice or not message.author.voice.channel:
                    message_content += "(OBISERVATION: HE IS NOT IN A VOICE CHANNEL!)"
                else:
                    voice_channel = message.guild.voice_client

                    if voice_channel: #If voice is already in the channel, move him
                        if voice_channel.is_connecting():
                            return
                        elif voice_channel.channel != channel:
                            await voice_channel.move_to(channel)
                    else:
                        await message.author.voice.channel.connect(reconnect=True)
            
            response = await self.generate_response(message_content, message.author.display_name, message.attachments)
            
            await message.channel.send(response)
        elif is_silly(message.content):
            response = await self.generate_response("Dont't talk or start a conversation just do something cute!")

            await message.channel.send(response)

    async def on_voice_state_update(self, member, before, after) -> None:
        member_voice_client = member.guild.voice_client
        if not member_voice_client:
            return
        
        if before.channel and before.channel == member_voice_client.channel:
            voice_channel = before.channel
            
            if not check_for_humans(voice_channel):
                # print(f"The channel #{voice_channel.name} is now empty!")
                
                await voice_channel.guild.voice_client.disconnect()


    async def check_reply(self, message: discord.Message) -> bool:
        """
        Takes a message and checks if it's replying/mentioning the bot.

        :param message: The discord message to be checked
        :type message: discord.Message

        :returns: If the message mentions or reply the bot
        :rtype: bool
        """
        if self.user.mention in message.content:
            return True
        elif message.reference:
            referenced = await message.channel.fetch_message(message.reference.message_id)
            
            return referenced.author.id == self.user.id
        
        return False


    async def generate_response(self, message: str, author_name: str = "", attachments: list = []) -> str:
        """
        This function not only generate responses using the AI API
        but also handles the AI memory, image processing, the values for temperature and
        token size are used from the class

        :param message: is the user input to the ai
        :type message: str

        :param author_name: is the author name, so the bot can know who is texting
        :type author_name: str

        :param attachments: is a list of all the media append to the message
        :type attachments: list

        :returns: text with the ai response
        :rtype: list
        """
        # Append to the right
        content = ""
        if len(attachments) > 0:
            author_message = message
            if author_name and not author_name.isspace():
                author_message = f"{author_name} says: \"{message}\"" 

            content = await self.process_attatchments(author_message, attachments)
        elif author_name and not author_name.isspace():
            content = f"{author_name} says: \"{message}\"" 
        else:
            content = message

        self.history.append({
            "role": "user",
            "content": content
        })
        # print(self.history)

        response = self.ai.chat(
            model=self.model,
            messages=self.history,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        self.history.append({
            "role": "assistant",
            "content": response.message.content[0].text
        })

        # Remove from the left
        if len(self.history) > 1 + self.MEMORY_SIZE:
            del self.history[1:2] #! Don't remove first element it is bot setting
            
        return response.message.content[0].text
    
    async def process_attatchments(self, message: str, attachments: list) -> list[dict]:
        """
        Takes a message and a list of attechments to covert into base64 and automaticaly generate the prompt

        :param message: A string with the user message
        :type message: str

        :param attachments: The attachments that the user sent to the program
        :type attachments: list

        :returns: A list of dictionaries that represents the user prompt
        :rtype: list[dict]
        """
        prompt: list[dict] = [
            {
                "type": "text",
                "text": message
            }
        ]

        for attachment in attachments:
            if attachment.content_type and attachment.content_type.startswith("image"): # check mimetype
                # print("Found image!")
                byte_image: bytes = await attachment.read()
                base64_image = to_base64(byte_image) # Make image base64 so i can send to the model
                prompt.append({
                    "type": "image_url",
                    "image_url": { 
                        "url": f"data:{attachment.content_type};base64,{base64_image}" 
                    }
                })
        
        return prompt


def replace_id_with_displayname(message: discord.Message) -> str:
    """
    Gets the user message and returns a all the ids replaced by their user names version

    :param message: The user massed to be scanned
    :type message: discord.Message

    :returns: The version of message with ids replaced by usernames 
    :rtype: str
    """
    content = message.content
    user_ids = get_ids(content)

    for i in user_ids:
        member = message.guild.get_member(int(i))
        content = content.replace(f"<@{i}>", member.display_name)
    
    return content


def check_for_humans(channel: discord.VoiceChannel) -> bool:
    """
    Looks trought a voice channel cehecking if there's any humans.

    :param channel: The voice channel to lookup
    :type channel: discord.VoiceChannel

    :returns: If there's any human in the channel
    :rtype: bool
    """
    return len([m for m in channel.members if not m.bot]) != 0


def to_base64(bytes_seq: bytes) -> str:
    """
    :param bytes_seq: The bytes sequences to be converted
    :type bytes_seq: bytes

    :returns: Base64 encoded string version of bytes_seq
    :rtype: str
    """
    return base64.b64encode(bytes_seq).decode("utf-8")


def get_ids(message: str) -> list[str]:
    """
    Takes a string and return all the ids on it, a id has a format of:
    <@1234567890>
    
    :param message: A string to extract all the ids
    :type message: str

    :returns: A list with the id's numbers
    :rtype: list[str]
    """
    user_ids = re.findall(r"<@!?(\d+)>", message)
    return user_ids


def is_silly(message: str) -> bool:
    tokenized_message = message.lower()
    silly_words = [ "uwu", "owo", "twt", "-w-", ":3", "^^", "^_^" ]
    return any(word in tokenized_message for word in silly_words)


if __name__ == "__main__":
    keep_alive()
    main()
