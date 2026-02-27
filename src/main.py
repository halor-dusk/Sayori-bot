import discord
from google import genai
from google.genai import types
import envar

import re

def main() -> None:
    print(f"""
Bot token is: '{envar.BOT_TOKEN}'
Api key is: '{envar.AI_KEY}'
""")

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    bot = SayoryBot(intents=intents)
    bot.run(envar.BOT_TOKEN)

class SayoryBot(discord.Client):
    async def on_ready(self) -> None:
        self.ai = genai.Client(api_key=envar.GEMINY_KEY)

        self.model = "gemini-3-flash-preview"
        self.personality = "You're Sayori from doki doki lieterature club and someone says:"
        self.answer_format = "You should answer in a short message without quots!"
        self.main_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level="medium"),
            system_instruction=self.personality + ", " + self.answer_format,
            temperature=1
        )
        self.main_chat =self.ai.chats.create(
            model=self.model,
            config=self.main_config
        )

        print(f"""
Logged in as: '{self.user}'
Ai model: {self.model}
""")

    async def on_message(self, message: discord.Message) -> None:
        print(f"Raw message from {message.author.name}: '{message.content}'")

        if message.author == self.user:
            return # The bot should not respond to its own messages

        elif await self.check_reply(message):
            print("Processing message...")
            message_content = replace_ids_with_displayname(message)
            print(
                f"Processed message: '{message_content}'", 
                "Thinking...",
                sep="\n"
            )

            response = self.main_chat.send_message(message_content)

            await message.channel.send(response.text)

        elif is_silly(message.content):
            response = self.ai.models.generate_content(
                model=self.model,
                contents="Dont't talk or start a conversation just do something cute!",
                config=self.main_config
            )

            await message.reply(response.text)
        
    
    async def check_reply(self, message: discord.Message) -> bool:
        if self.user.mention in message.content:
            return True
        
        if message.reference:
            referenced = await message.channel.fetch_message(message.reference.message_id)
            
            return referenced.author.id == self.user.id
        
        return False
        

def replace_ids_with_displayname(message: discord.Message) -> str:
    content = message.content
    user_ids = get_ids(content)

    for i in user_ids:
        # print(f"Id: {i}")
        member = message.guild.get_member(int(i))
        # print(f"Member: {member}")
        content = content.replace(f"<@{i}>", member.display_name)
    
    return content

def get_ids(message: str) -> list[str]:
    user_ids = re.findall(r"<@!?(\d+)>", message)
    return user_ids

def is_silly(message: str) -> bool:
    tokenized_message = message.lower().split()
    silly_words = [ "uwu", "owo", "twt", "-w-", ":3", "^^", "^_^" ]
    return any(word in tokenized_message for word in silly_words)

if __name__ == "__main__":
    main()
