import toml
import asyncio
import time
import concurrent.futures
import threading

import streamlit as st

from queries import llama_chat_stream, llama_chat_query, stable_diffusion_query
from streamer import streamer_wrapper

# Configure Streamlit page.
st.set_page_config(page_title="Storyteller",
                   page_icon=":open_book:",
                   layout="wide",
                   menu_items={"Get help": "https://github.com/uhudo/storyteller",
                               "About": "Storyteller is AI powered adventure story"
                                        "where you participate in the story telling.\n\nv0.1.0"})


# Function to run the event loop in a separate thread.
def start_event_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


# Schedule new task in the separate thread.
def start_task(task):
    # Set state that tasks are running.
    st.session_state.running = True
    # Submit task to the event loop and save their futures.
    st.session_state.tasks.add(
        asyncio.run_coroutine_threadsafe(task, st.session_state.loop)
    )
    st.session_state.task_count += 1
    print("Task started", st.session_state.task_count)


# Process the scheduling and responses of the LLM and SD server.
def storyteller_process(prompt, response=None):
    if response is None:
        # First lock user input.
        st.session_state.llm_lock = True
        print("User prompt :", st.session_state.llm_count)
        # Add prompt to the conversation.
        st.session_state.llm_conversation.append({"role": "user",
                                                  "content": prompt})
        # Add prompt to the enhanced version conversation and send to the LLM.
        st.session_state.llm_enhanced.append({"role": "user",
                                                      "content": "This are the ideas from the listener." 
                                                                 "Continue the story in a short 50 word"
                                                                 "response based on their input:"
                                                                 + prompt
                                              })
        start_task(streamer_wrapper(llama_chat_stream,
                                    (st.session_state.llama_chat_endpoint,
                                     st.session_state.llm_conversation,
                                     250,
                                     "stream",
                                     st.session_state.llm_count)))
        # Generate prompt for image generation. By sending it first to the LLM.
        sd_messages = [
            {"role": "system", "content": "You generate prompts for AI image generation based on a story."}]
        sd_prompt = "Generate short 20 words prompt based on the story." \
                    "Extract only the important information.\n" + \
                    st.session_state.llm_conversation[-1]["content"] + "\n" + \
                    "new prompt:"
        sd_messages.append({"role": "user", "content": sd_prompt})
        start_task(llama_chat_query(st.session_state.llama_chat_endpoint,
                                    sd_messages,
                                    30,
                                    "sd_prompt",
                                    st.session_state.llm_count))
        st.session_state.llm_count += 1
    else:
        if response["index"] == "stream":
            # When receiving stream response.
            if st.session_state.llm_conversation[-1]["role"] == "user":
                # Append to conversation on first response.
                st.session_state.llm_conversation.append({"role": "assistant", "content": response["data"]})
            else:
                # Add to the content.
                st.session_state.llm_conversation[-1]["content"] += response["data"]
            if response["final"]:
                # When the stream finishes unlock the user input.
                print("Stream ended", st.session_state.llm_count)
                st.session_state.llm_lock = False
        if response["index"] == "image":
            # Received new generated image.
            print("Image", st.session_state.image_count)
            # Save it first.
            image = "data/image" + str(st.session_state.image_count) + ".png"
            with open(image, 'wb') as f:
                f.write(response["data"])
            # Set it as a new image to display.
            st.session_state.image = image
            st.session_state.image_count += 1
        if response["index"] == "sd_prompt":
            # Generated stable diffusion prompt.
            print("Stable diffusion prompt:\n", response["data"])
            # Query a new image.
            start_task(stable_diffusion_query(st.session_state.stable_diffusion_endpoint,
                                              response["data"]+"artistic, fantasy",
                                              "cartoon, realism",
                                              "image",
                                              st.session_state.image_count))
        if response["index"] == "story_start":
            # When story is being set up for the first time.
            if len(st.session_state.llm_conversation) == 0:
                # Append to conversation on first response.
                st.session_state.llm_conversation.append({"role": "assistant", "content": response["data"]})
            else:
                # Add to the content.
                st.session_state.llm_conversation[-1]["content"] += response["data"]
            if response["final"]:
                # When final streaming response is received.
                print("Story started")
                # Add new lines to be displayed.
                st.session_state.llm_conversation[-1]["content"] += "\n\n"
                # Append first generated response from LLM and another prompt about the characters.
                st.session_state.llm_enhanced.append(st.session_state.llm_conversation[-1])
                st.session_state.llm_enhanced.append({"role": "user",
                                                      "content": "Imagine an adventure on for one or"
                                                                 "multiple adventurers. In 70 word shortly"
                                                                 "introduce the adventurers to the listener and"
                                                                 "position them in the world where their adventure"
                                                                 "starts."}
                                                     )
                # Start new streaming request to the LLM.
                start_task(streamer_wrapper(llama_chat_stream,
                                            (st.session_state.llama_chat_endpoint,
                                             st.session_state.llm_enhanced,
                                             140,
                                             "stream",
                                             st.session_state.llm_count)))
                # Generate prompt for image generation. By sending it first to the LLM.
                sd_messages = [
                    {"role": "system", "content": "You generate prompts for AI image generation based on a story."}]
                sd_prompt = "Generate short 20 words prompt based on the world environment description." \
                            "Extract only the important words.\n" + \
                            st.session_state.llm_conversation[-1]["content"] + "\n" + \
                            "new prompt:"
                sd_messages.append({"role": "user", "content": sd_prompt})
                start_task(llama_chat_query(st.session_state.llama_chat_endpoint,
                                            sd_messages,
                                            30,
                                            "sd_prompt",
                                            st.session_state.llm_count))


# Display the story.
def conversation_write():
    for message in st.session_state.llm_conversation:
        if message["role"] == "system":
            pass
        else:
            with c_conversation.chat_message(message["role"]):
                st.markdown(message["content"])


# Load configuration.
if 'config' not in st.session_state:
    config = toml.load("config.toml")
    st.session_state.llama_chat_endpoint = config["streamlit"]["llama_chat_endpoint"]
    st.session_state.stable_diffusion_endpoint = config["streamlit"]["stable_diffusion_endpoint"]
# Prepare thread for asynchronous tasks.
if 'thread' not in st.session_state:
    # Initialize task set.
    st.session_state.tasks = set()
    # Initialize variable for when tasks are running.
    st.session_state.running = False
    # Create a new event loop and start it in a new thread.
    st.session_state.loop = asyncio.new_event_loop()
    st.session_state.thread = threading.Thread(
        target=start_event_loop,
        args=(st.session_state.loop,),
        daemon=True
    )
    st.session_state.thread.start()
# Initialize counters for debugging.
if "task_count" not in st.session_state:
    st.session_state.task_count = 0
    st.session_state.llm_count = 0
# Initialize LLM conversation state.
if "image" not in st.session_state:
    st.session_state.image = None
    st.session_state.image_count = 0
# Initialize LLM conversation.
if "llm_conversation" not in st.session_state:
    st.session_state.llm_conversation = []
    # Start a new story.
    st.session_state.llm_enhanced = [{"role": "system",
                                      "content": "You are a storyteller. You tell a fantasy story and"
                                                 "include the ideas rom your listeners."
                                                 "You don't ask questions and don't use bullet points."},
                                     {"role": "user",
                                      "content": "You imagine a new fantasy story."
                                                 "In a shor description in 50 words you"
                                                 "start to tell about the world where the story is set."
                                      }]
    # Request streaming response from the LLM with the story begging.
    start_task(streamer_wrapper(llama_chat_stream,
                                (st.session_state.llama_chat_endpoint,
                                 st.session_state.llm_enhanced,
                                 150,
                                 "story_start",
                                 st.session_state.llm_count)))
    # Initially lock the user input.
    st.session_state.llm_lock = True


# Write the title.
st.header("Storyteller :open_book:", divider="blue")
st.write("Participate in the storytelling. You decide how it unfolds.")

# Make two columns one for chat and one for image.
col1, col2 = st.columns(2)
with col1:
    c_conversation = st.container(height=450)
    # Write the conversation.
    conversation_write()
    # Prepare container for chat input.
    # Chat input.
    prompt = st.chat_input(placeholder="Your input:",
                           key="chat_input",
                           disabled=st.session_state.llm_lock
                           )
    if prompt:
        # If user prompt is received process it.
        storyteller_process(prompt, response=None)
with col2:
    if st.session_state.image is not None:
        st.image(st.session_state.image, use_column_width="always")

# Check if tasks are running and update results.
if st.session_state.running:
    # Check if all tasks are done.
    done, not_done = concurrent.futures.wait(
        st.session_state.tasks,
        timeout=0.2,
        return_when=concurrent.futures.ALL_COMPLETED
    )
    if done:
        # print("Task completed", st.session_state.task_count)
        # Retrieve results.
        st.session_state.tasks = not_done
        for future in done:
            res = future.result()
            # print("Result", res["index"], res['count'])
            # Process the results.
            storyteller_process(None, response=res)
            if "task" in res:
                st.session_state.tasks.add(res["task"])
        # print("Remaining tasks", st.session_state.tasks)
        if len(st.session_state.tasks) == 1:
            # Additional delay if only one task is running as the streaming responses are too quick.
            time.sleep(0.2)
    if len(st.session_state.tasks) == 0:
        # If no more tasks are running set running flag to false.
        st.session_state.running = False
    # Rerun the script if something was processed.
    st.rerun()
