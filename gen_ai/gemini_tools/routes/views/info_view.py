import json
import random
from flet import *
from typing import Union
from views.Router import Router, DataStrategyEnum
from State import global_state

items_available = random.randint(1,8)

def InfoView(page: Page, router: Union[Router, str, None] = None):
  if router and router.data_strategy == DataStrategyEnum.STATE:
    data = global_state.get_state_by_key("data").get_state()

  # cat_3_q = [json.loads(element) for element in data["cat_3_questions"]]
  # print(cat_3_q[0]["rephrased_question"])

  image_container = Container(
      padding=14,
      alignment=alignment.bottom_center,
      content=Image(
          data["public_cdn_link"],
          fit=ImageFit.CONTAIN
      ),
      on_click=lambda x: page.launch_url(data["listing_id"])
  )

  #Left Panel Content
  left = Container(
      padding=14,
      # height=page.height * .90,
      width=page.width * .50,
      col={"sm": 6, "md": 6, "xl": 6},
      content=image_container
  )

  # Right Panel Content (chat)
  chat_text_input = Container(
      expand=True,
      content=TextField(
          hint_text="Looking for specific info? Ask Chatsy!",
          hint_style=TextStyle(size=14),
          multiline=True,
          min_lines=1,
          max_lines=10,
          shift_enter=True,
          #on_submit=execute
      )
  )

  # Right Panel Content (chat)
  chatbot_window = Container(
      padding=padding.only(left=15, right=15),
      width=page.width * .50,
      content=Row(
          vertical_alignment=CrossAxisAlignment.CENTER,
          controls=[
              Container(
                  height=30,
                  width=30,
                  content=Image(src="https://gcpetsy.sonrobots.net/artifacts/etsymate.png", fit=ImageFit.CONTAIN),
              ),
              chat_text_input,
              IconButton(
                  icon=icons.SEND,
                  icon_color=colors.DEEP_ORANGE_400,
                  # on_click=execute
              )
          ]
      )
  )

  response = Text()

  # Right Panel Content (chat)
  chatbot_response = Container(
      padding=15,
      border=border.all(1, color=colors.DEEP_ORANGE_400),
      border_radius=14,
      width=page.width * .50,
      content=Column(
          alignment=MainAxisAlignment.START,
          spacing=5,
          controls=[
              Text("Chatsy: ", style=TextStyle(color=colors.DEEP_ORANGE_400, weight=FontWeight.BOLD)),
              response,
              relevant_text:=Text("Here are some other relevant listings:", visible=False),
              response_image_panel:=Container(
                  visible=False,
                  content=Row(expand=1, wrap=False, scroll=ScrollMode.ALWAYS)
              )
          ]
      ),
      visible=False
  )

  panel = ExpansionPanelList(
      expand_icon_color=colors.DEEP_ORANGE_400,
      elevation=0,
      divider_color=colors.DEEP_ORANGE_400,
      controls=[
          ExpansionPanel(
              header=ListTile(title=Text("Item Details", size=14)),
              content=Container(
                  padding=10,
                  content=Column(
                      alignment=MainAxisAlignment.CENTER,
                      horizontal_alignment=CrossAxisAlignment.CENTER,
                      controls=[Text(line.strip(), selectable=True) for line in data["description"].split('\\n')]
                  ),
              ),
          )
      ]
  )

  def create_image_containers(image_uris):
    return [
        Container(
            content=Image(
                src=image,
                width=120,
                height=120,
                fit=ImageFit.CONTAIN,
                border_radius=border_radius.all(10)
            ),
            data=image,
            #on_click=navigate_to_search_page
        ) for image in image_uris
    ]

  def button_message(e):
    chat_text_input.content.value = e.control.data["question"].strip()
    if "image_urls" not in e.control.data:
      chatbot_response.content.controls[1].value = e.control.data["answer"].strip()
    else:
      chatbot_response.content.controls[1].value = e.control.data["answer"].strip()
      response_image_panel.content.controls.extend(create_image_containers(e.control.data["image_urls"]))
    chatbot_response.visible = True
    right.update()



  # Right Panel Content (main)
  right = Container(
      expand=True,
      col={"sm": 6, "md": 6, "xl": 6},
      margin=margin.only(right=30, top=30),
      padding=18.0,
      content=Column(
          alignment=MainAxisAlignment.CENTER,
          horizontal_alignment=CrossAxisAlignment.CENTER,
          expand=True,
          # scroll=ScrollMode.ALWAYS,
          spacing=10,
          controls=[
              Text(f"Low in stock, only {items_available} left",
                   color=colors.DEEP_ORANGE_400,
                   size=16,
                   weight=FontWeight.BOLD,
                   ),
              Text(f'$ {data["price_usd"]:.2f}', weight=FontWeight.BOLD, size=20),
              Text(data["generated_title"], selectable=True, size=18),
              Text(data["title"], selectable=True, size=14),
              Text(
                  spans=[
                      TextSpan("Description: ", TextStyle(weight=FontWeight.BOLD)),
                      TextSpan(data["generated_description"].strip())
                  ],
                  selectable=True,
              ),
              panel,
              chatbot_window,
              chatbot_response,
              conv:=Row(
                  wrap=True,
                  scroll=ScrollMode.AUTO,
                  controls=[
                      ElevatedButton(
                          text=question,
                          color="black",
                          bgcolor="#E3F2FD",
                          style=ButtonStyle(
                              shape=RoundedRectangleBorder(radius=25),
                              padding=15,
                          ),
                          data={"question": question, "answer":  answer},
                          on_click=button_message
                      )
                  for question, answer in zip(data["q_cat_1"], data["a_cat_1"])
                  ]
                  +
                  [
                    ElevatedButton(
                        text=question,
                        color="black",
                        bgcolor=colors.RED_100,
                        style=ButtonStyle(
                            shape=RoundedRectangleBorder(radius=25),
                            padding=15,
                        ),
                        data={"question": question, "answer":  answer},
                        on_click=button_message
                    )
                    for question, answer in zip(data["q_cat_2"], data["a_cat_2"])
                  ]
                  # +
                  # [
                  #     ElevatedButton(
                  #         text=i["rephrased_question"].strip(),
                  #         color="black",
                  #         bgcolor=colors.YELLOW_50,
                  #         style=ButtonStyle(
                  #             shape=RoundedRectangleBorder(radius=25),
                  #             padding=15,
                  #         ),
                  #         data={"question": i["rephrased_question"], "answer":  i["answer"], "image_urls": i["rec_image_urls"]},
                  #         on_click=button_message
                  #     ) for i in cat_3_q
                  # ]
              )
          ]
      )
  )

  def go_home(e):
    page.go("/")

  # Bottom App Bar
  bottom_app_footer = BottomAppBar(
      bgcolor=colors.TRANSPARENT,
      content=Row(
          alignment=MainAxisAlignment.START,
          controls=[
              IconButton(
                  icon=icons.ARROW_BACK_IOS_NEW,
                  icon_color=colors.DEEP_ORANGE_400,
                  on_click=lambda _: page.go("/")
              )
          ]
      )
  )

  page.appbar = bottom_app_footer
  page.update()

  return Column(
      expand=True,
      scroll=ScrollMode.AUTO,
      alignment=MainAxisAlignment.CENTER,
      controls=[
          ResponsiveRow(
              controls=[
                  left,
                  right
              ]
          )
      ]
  )