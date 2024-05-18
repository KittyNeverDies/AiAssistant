import asyncio

import whisper as stt
import flet as ft
import g4f

is_recording = False
stt_model = stt.load_model("base")
llm_model = "gpt-3.5-turbo"
chat_history = []


class ChatMessage(ft.Row):
    """
    Class of chat message object, selected from
    flet documentation about creating real time chat
    """

    def remove_message(self) -> None:
        """
        Removes message from chat history
        :return:
        """
        chat_history.pop()


    def __init__(self, message: dict):
        super().__init__()
        self.vertical_alignment = "start"
        self.controls = [
            ft.CircleAvatar(
                content=ft.Text(self.get_initials(message["name"])),
                color=ft.colors.WHITE,
                bgcolor=self.get_avatar_color(message["name"]),
            ),
            ft.Column(
                [
                    ft.Text(message["name"]),
                    ft.Markdown(message["text"], selectable=True,
                                extension_set="gitHubWeb",
                                code_theme="atom-one-light", width=message["width"]),
                ],
                tight=True,
                spacing=2,
            ),

        ]

    @staticmethod
    def get_initials(user_name: str) -> str:
        """
        Gets initials by username.
        :param user_name: Name of user
        :return: Initials :)
        """
        return user_name[:1].capitalize()

    @staticmethod
    def get_avatar_color(user_name: str) -> str:
        """
        Gets color of avatar
        :param user_name: Name of user
        :return: Color
        """
        colors_lookup = [
            ft.colors.AMBER,
            ft.colors.BLUE,
            ft.colors.BROWN,
            ft.colors.CYAN,
            ft.colors.GREEN,
            ft.colors.INDIGO,
            ft.colors.LIME,
            ft.colors.ORANGE,
            ft.colors.PINK,
            ft.colors.PURPLE,
            ft.colors.RED,
            ft.colors.TEAL,
            ft.colors.YELLOW,
        ]
        return colors_lookup[hash(user_name) % len(colors_lookup)]


async def main(page: ft.Page) -> None:
    """
    Current page function :P
    :param page: Main page object
    :return: None
    """

    page.title = "AI Assistant"
    page.splash = ft.ProgressBar(visible=False)

    async def on_resize(data: ft.ControlEvent) -> None:
        """
        On resize handler, makes text a little bit readable.
        TODO: Make it better in future
        :param data: Data coming from event
        :return: Nothing
        """
        print(data, page.window_width)
        for message in page.controls[0].content.controls:
            message.controls[1].controls[
                1].width = page.window_width - 20 if page.window_width > 20 else page.window_width
        await page.update_async()

    page.on_resize = on_resize

    async def handle_recording_button_click(event: ft.ControlEvent) -> None:
        """
        Handles recording button click
        :param event: Event on clicking
        :return: None
        """
        global is_recording, stt_model, llm_model, chat_history

        if not is_recording:
            # Set status for recording
            event.control.icon = ft.icons.STOP_CIRCLE_ROUNDED
            event.control.text = "Stop Listening"

            # Start recording audio
            await audio_rec.start_recording_async(f"voice.wav")
            await page.update_async()

            # Changing state
            is_recording = True
        elif is_recording:
            try:
                # Set status for not recording
                page.splash.visible = True
                event.control.icon = ft.icons.RECORD_VOICE_OVER_ROUNDED
                event.control.text = "Start Listening"

                # Updating page & stoping recording
                await page.update_async()
                await audio_rec.stop_recording_async()

                # load audio and pad/trim it to fit 30 seconds
                result = stt_model.transcribe("voice.wav")

                page.controls[0].content.controls.append(
                    ChatMessage(message={
                        "name": "You",
                        "text": result["text"],
                        "width": page.width - 20 if page.width > 20 else page.width
                    })
                )

                await page.update_async()

                # Geneate response from model of g4f
                text = await g4f.ChatCompletion.create_async(
                    model=llm_model,
                    messages=chat_history + [{"role": "user", "content": result["text"]}],
                )

                page.controls[0].content.controls.append(
                    ChatMessage(message={
                        "name": llm_model.replace("-", " "),
                        "text": text,
                        "width": page.width - 20 if page.width > 20 else page.width
                    })
                )

                chat_history.append({"role": "user", "content": result["text"]})
                chat_history.append({"role": "assistant", "content": text})
                await page.update_async()

                # Updating page
                await page.update_async()
                await asyncio.sleep(0.5)

                # Hiding splash animation
                page.splash.visible = False
                await page.update_async()

            except Exception as e:
                page.controls[0].content.controls.append(
                    ChatMessage(message={
                        "name": llm_model.replace("-", " "),
                        "text": "Exception while generating your response happened: {}".format(e),
                        "width": page.width - 20 if page.width > 20 else page.width
                    })
                )
                page.splash.visible = False
                page.update()
            is_recording = False

    async def handle_select_stt_model(event: ft.ControlEvent) -> None:
        """
        Handles selecting STT model
        :param event: Event on selecting
        :return: None
        """
        global stt_model
        stt_model = stt.load_model(event.data.lower())

    async def handle_select_lmm_model(event: ft.ControlEvent) -> None:
        """
        Handles selecting LLM model
        :param event: Event on selecting
        :return: None
        """
        global llm_model
        llm_model = event.data

    async def handle_clear_button_click(event: ft.ControlEvent) -> None:
        """
        Handles clearing chat history
        :param event: Event on clicking
        :return: None
        """
        global chat_history
        chat_history = []
        page.controls[0].content.controls = []
        await page.update_async()

    async def send_message_click(event: ft.ControlEvent) -> None:
        """
        Send message on click
        :param event: Event on clicking
        :return: None
        """
        global chat_history, llm_model
        try:
            page.splash.visible = True
            page.controls[0].content.controls.append(
                ChatMessage(message={
                    "name": "You",
                    "text": message_field.value,
                    "width": page.width - 20 if page.width > 20 else page.width
                })
            )
            await page.update_async()

            text = await g4f.ChatCompletion.create_async(
                model=llm_model,
                messages=chat_history + [{"role": "user", "content": message_field.value}],
            )

            page.controls[0].content.controls.append(
                ChatMessage(message={
                    "name": llm_model.replace("-", " "),
                    "text": text,
                    "width": page.width - 20 if page.width > 20 else page.width
                })
            )
            await page.update_async()
            await asyncio.sleep(1)

            page.splash.visible = False
            await page.update_async()

            chat_history.append({"role": "user", "content": message_field})
            chat_history.append({"role": "assistant", "content": text})
        except Exception as e:
            page.controls[0].content.controls.append(
                ChatMessage(message={
                    "name": llm_model.replace("-", " "),
                    "text": "Exception while generating your response happened: {}".format(e),
                    "width": page.width - 20 if page.width > 20 else page.width
                })
            )
            page.splash.visible = False
            page.update()

    audio_rec = ft.AudioRecorder(
        audio_encoder=ft.AudioEncoder.WAV,
    )

    page.appbar = ft.AppBar(
        title=ft.Text("AI Assistant"),
        center_title=True,
        bgcolor=ft.colors.SURFACE_VARIANT,
        actions=[
            ft.IconButton(ft.icons.CLEAR_ROUNDED, on_click=handle_clear_button_click, tooltip="Clear chat history"),
            ft.PopupMenuButton(
                items=[
                    ft.PopupMenuItem(
                        content=ft.Column([
                            ft.Container(
                                content=ft.Text("Select your STT model")
                            ),
                            ft.Container(
                                content=ft.Dropdown(
                                    width=300,
                                    options=[ft.dropdown.Option(model) for model in stt.available_models()],
                                    height=60,
                                    on_change=handle_select_stt_model,

                                )
                            )
                        ])
                    ),
                    ft.PopupMenuItem(
                        content=ft.Column([
                            ft.Container(
                                content=ft.Text("Your model LLM from g4f")
                            ),
                            ft.Container(
                                content=ft.Dropdown(
                                    width=300,
                                    options=[ft.dropdown.Option(model) for model in g4f.models._all_models],
                                    height=60,
                                    value="gpt-3.5-turbo",
                                    on_change=handle_select_lmm_model,
                                )
                            )
                        ])
                    ),
                ]
            ),
        ],
    )

    message_field = ft.TextField(
        hint_text="Write a message...",
        autofocus=True,
        shift_enter=True,
        filled=True,
        expand=True,
        on_submit=send_message_click,
        bgcolor=ft.colors.TRANSPARENT,
        border_radius=5,
        border_width=1,
        border_color=ft.colors.SURFACE_VARIANT,

    )

    page.overlay.append(audio_rec)
    await page.update_async()

    chat_history_list = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,

    )
    await page.add_async(
        ft.Container(
            content=chat_history_list,
            border_radius=5,
            padding=10,
            expand=True,
        ),
        ft.Row(
            [
                message_field,
                ft.IconButton(
                    icon=ft.icons.SEND_ROUNDED,
                    tooltip="Send message",
                    on_click=send_message_click,
                ),
                ft.IconButton(
                    icon=ft.icons.RECORD_VOICE_OVER_ROUNDED,
                    tooltip="Record message",
                    on_click=handle_recording_button_click,
                ),
            ]
        ),
    )


ft.app(target=main)
