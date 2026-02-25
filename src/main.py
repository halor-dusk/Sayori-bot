import discord
import envar

def main() -> None:
    print("Bot token is: ", envar.BOT_TOKEN)

    intents = discord.Intents.default()
    intents.message_content = True
    bot = SayoryBot(intents=intents)
    bot.run(envar.BOT_TOKEN)

class SayoryBot(discord.Client):
    async def on_ready(self) -> None:
        print(f"Logged in as {self.user}")

    async def on_message(self, message: discord.Message) -> None:
        print(f"> {message.author.name}: {message.content}")

        if message.author.name == self.user.name:
            return # The bot should not respond to its own messages

        if self.user.mention in message.content:
            await message.channel.send(f"Hello, {message.author.mention}! How can I help you?")

if __name__ == "__main__":
    main()
