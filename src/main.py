import discord
import cohere

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
        self.ai = cohere.ClientV2(envar.AI_KEY)
        self.model = "command-a-03-2025"
        self.personality = "You're Sayori from doki doki lieterature club"
        self.answer_format = "You should answer without quots!"
        # Memory size in messages, 2 means 1 user message and 1 bot answer
        self.MEMORY_SIZE = 16*2

        # Prompt works like the settings and the memory for the bot
        # also used to send the message to the bot
        self.prompt: list[dict[str, str]] = [
            {
                "role": "system",
                "content": self.personality + ", " + self.answer_format
            }
        ]

        print(f"Logged in as: '{self.user}'")

    async def on_message(self, message: discord.Message) -> None:
        print(f"Raw message from {message.author.name}: '{message.content}'")

        if message.author == self.user:
            return # The bot should not respond to its own messages
        elif await self.check_reply(message):
            message_content = replace_id_with_displayname(message)
            print(f"Processed message: '{message_content}'")

            self.prompt.append({
                "role": "user",
                "content": f"{message.author.display_name} says: \"{message_content}\""
            })
            print("Thinking...")
            
            response = self.ai.chat(
                model=self.model,
                messages=self.prompt
            )

            self.prompt.append({
                "role": "assistant",
                "content": response.message.content[0].text
            })
            
            # Remove from the left
            if len(self.prompt) >= 1 + self.MEMORY_SIZE:
                del self.prompt[1:2] # Don't remove first element it is bot setting
            
            await message.channel.send(response.message.content[0].text)

        elif is_silly(message.content):
            response = self.ai.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self.personality + ", " + self.answer_format
                    },
                    {
                        "role": "user",
                        "content": "dont't talk or start a conversation just do something cute!"
                    }
                ]
            )

            await message.channel.send(response.message.content[0].text)
        
    async def check_reply(self, message: discord.Message) -> bool:
        if self.user.mention in message.content:
            return True
        
        if message.reference:
            referenced = await message.channel.fetch_message(message.reference.message_id)
            
            return referenced.author.id == self.user.id
        
        return False

def replace_id_with_displayname(message: discord.Message) -> str:
    content = message.content
    user_ids = get_ids(content)

    for i in user_ids:
        member = message.guild.get_member(int(i))
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
