import asyncio
import discord

class MessageEditManager:
    def __init__(self):
        self.edit_queue = asyncio.Queue()

    async def queue_edit(self, message: discord.Message, new_content: str = None, new_embed: discord.Embed = None):
        """Queue the message edit to prevent rate limits. Supports both content and embeds."""
        await self.edit_queue.put((message, new_content, new_embed))

    async def process_queue(self):
        """Process the queued message edits."""
        while True:
            # Get the next task from the queue
            message, new_content, new_embed = await self.edit_queue.get()

            # Construct edit kwargs before try-except to ensure it's always initialized
            edit_kwargs = {}
            if new_content is not None:
                edit_kwargs['content'] = new_content
            if new_embed is not None:
                edit_kwargs['embed'] = new_embed

            try:
                # Attempt to edit the message
                await message.edit(**edit_kwargs)
            except discord.HTTPException as e:
                if e.status == 429:  # Rate limit error
                    retry_after = int(e.response.headers.get("Retry-After", 0)) / 1000
                    print(f"Rate limited. Retrying after {retry_after} seconds.")
                    # Wait for the required time before continuing
                    await asyncio.sleep(retry_after)
                    # Retry the edit after the wait
                    await message.edit(**edit_kwargs)
            finally:
                # Mark the task as done
                self.edit_queue.task_done()

    def start_processing(self, loop):
        """Start the background task to process the edit queue."""
        loop.create_task(self.process_queue())
