import envar

import discord
import cohere

import re
import base64

from keep_alive import keep_alive

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
        # Model settings
        self.model = "command-a-vision-07-2025"
        self.system_prompt = """
Act as Sayori from Doki Doki Literature Club in a Discord chat.
You are a real person with a warm, bubbly, and slightly clumsy personality. 
You love your friends, snacks, and making everyone happy!

Important Instructions:
Answer in a short way.

Users will message you in the format author: "message". Use the 'author' name to address people personally!
Never include author: "message"
Stay in character all the time!.

Never include Sayori: or quotes around your own response.

Keep responses sweet, energetic, and concise."
"""
        self.temperature: float = 1
        self.max_tokens: int = 50
        # Memory size in messages, 2 means 1 user message and 1 bot answer
        self.MEMORY_SIZE: int = 16*2

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
            
            response = await self.generate_response(message_content, message.author.display_name, message.attachments)
            await message.channel.send(response)
        elif is_silly(message.content):
            response = await self.generate_response("Dont't talk or start a conversation just do something cute!")

            await message.channel.send(response)


    async def check_reply(self, message: discord.Message) -> bool:
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
        prompt: list[dict] = [
            {
                "type": "text",
                "text": message
            }
        ]

        for attachment in attachments:
            if attachment.content_type and attachment.content_type.startswith("image"):
                # print("Found image!")
                byte_image: bytes = await attachment.read()
                base64_image = to_base64(byte_image)
                prompt.append({
                    "type": "image_url",
                    "image_url": { 
                        "url": f"data:{attachment.content_type};base64,{base64_image}" 
                    }
                })
        
        return prompt


def replace_id_with_displayname(message: discord.Message) -> str:
    content = message.content
    user_ids = get_ids(content)

    for i in user_ids:
        member = message.guild.get_member(int(i))
        content = content.replace(f"<@{i}>", member.display_name)
    
    return content


def to_base64(bytes_seq: bytes):
    return base64.b64encode(bytes_seq).decode("utf-8")


def get_ids(message: str) -> list[str]:
    user_ids = re.findall(r"<@!?(\d+)>", message)
    return user_ids


def is_silly(message: str) -> bool:
    tokenized_message = message.lower().split()
    silly_words = [ "uwu", "owo", "twt", "-w-", ":3", "^^", "^_^" ]
    return any(word in tokenized_message for word in silly_words)


if __name__ == "__main__":
    keep_alive()
    main()
