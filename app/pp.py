import chainlit as cl


@cl.step
async def tool():
    # Simulate a running task
    await cl.sleep(2)

    return "Response from the tool!"


@cl.on_message
async def main(message: cl.Message):
    # Call the tool
    tool_res = await tool()

    # Send the final answer.
    await cl.Message(content="This is the final answer").send()
