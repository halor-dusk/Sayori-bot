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
        self.personality = "You're Sayori from doki doki lieterature club and someone says:"
        self.answer_format = "You should answer often in a short message without \"\"!"

        print(f"Logged in as: '{self.user}'")

    async def on_message(self, message: discord.Message) -> None:
        print(f"Raw message from {message.author.name}: '{message.content}'")

        if message.author == self.user:
            return # The bot should not respond to its own messages

        if self.user.mention in message.content:
            message_content = replace_id_with_displayname(message)
            print(f"Processed message: '{message_content}'")

            response = self.ai.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self.personality + ", " + self.answer_format
                    },
                    {
                        "role": "user",
                        "content": message_content
                    }
                ]
            )

            await message.channel.send(response.message.content[0].text)
        elif "uwu" in message.content.lower():
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

def replace_id_with_displayname(message: discord.Message) -> str:
    content = message.content
    user_ids = get_ids(content)

    for i in user_ids:
        print(f"Id: {i}")
        member = message.guild.get_member(int(i))
        print(f"Member: {member}")
        content = content.replace(f"<@{i}>", member.display_name)
    
    return content

def get_ids(message: str) -> list[str]:
    user_ids = re.findall(r"<@!?(\d+)>", message)
    return user_ids

if __name__ == "__main__":
    main()
