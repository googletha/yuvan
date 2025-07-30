"""
Async Task Handler for Yuvan
Handles async command processing with real-time speech synthesis
"""

import asyncio
from typing import Optional, Callable
from yuvan.task_handler import TaskHandler
from yuvan.silero_tts import speak_text_async, stop_speaking_async

class AsyncTaskHandler:
    def __init__(self):
        self.task_handler = TaskHandler()
        self.is_processing = False
    
    async def process_command_async(self, command: str, 
                                  completion_callback: Optional[Callable] = None):
        """Process command asynchronously with real-time speech"""
        if self.is_processing:
            await self.stop_processing()
        
        self.is_processing = True
        
        try:
            # Process command in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, self.task_handler.process_command, command
            )
            
            # Speak response asynchronously
            if response:
                await speak_text_async(response)
            
            if completion_callback:
                completion_callback(response)
                
        except Exception as e:
            print(f"Error in async processing: {e}")
        finally:
            self.is_processing = False
    
    async def stop_processing(self):
        """Stop current processing"""
        self.is_processing = False
        await stop_speaking_async()

# Global instance
async_handler = None

async def get_async_handler():
    global async_handler
    if async_handler is None:
        async_handler = AsyncTaskHandler()
    return async_handler

async def process_command_async(command: str, callback: Optional[Callable] = None):
    handler = await get_async_handler()
    await handler.process_command_async(command, callback) 