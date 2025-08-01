import csv
import random

from typing import Literal
from itertools import islice

from helpers_utilities import clean_up_unicode, has_value, is_yesno, is_int, shuffle, lower

random.seed(1) #give a fixed seed so that diffs don't make it look like we changed things every time we generate

dir_root = "./make"
dir_csv  = f"{dir_root}/CSV"

def create_conditions(args):
    if args: args = args.split(';')
    if args == [''] or not args: return {}
    
    args = [a.strip() for a in args]
    
    if len(args) == 3:
        left,comparison,right = args

    if len(args) == 2:
        left, right = args
        if ',' in right: right = [int(v) for v in right.split(",") if is_int(v)]
        comparison = "=" if not isinstance(right,list) else "in"

    return { "condition": [ left, comparison, right ] }

def create_nav_conditions(buttons:Literal["WhenCorrect","AfterTimeout","Never","WhenComplete"]=None,timeout=None,inputs=None):
    buttons = lower(buttons)
    inputs = inputs or []
    if 'puzzle' in list(map(lower,inputs)):
        return {"navigation_conditions": "wait_for_correct"}
    if timeout and buttons == "aftertimeout":
        return {"navigation_conditions": [{"wait_for_time": int(timeout)*1000}, "wait_for_click"]}
    if timeout:
        return {"navigation_conditions": [{"wait_for_time": int(timeout)*1000}]}
    if buttons == "whencorrect":
        return {"navigation_conditions": ["wait_for_correct", "wait_for_click"]}
    if buttons == "whencomplete":
        return {"navigation_conditions": ["wait_for_complete", "wait_for_click"]}
    return {}

def create_input(tipe, items=None, min=None, max=None, text=None):
    if not tipe: return None

    if items: items = clean_up_unicode(items).split("; ")
    if items == [""]: items = None

    tipe = lower(tipe)

    ## Based on what the input is, create input "add"
    if tipe == "picker"   : return {"type": "Picker", "items": items}
    if tipe == "slider"   : return {"type": "Slider", "min": min, "max": max, "others": items or ["^Prefer not to answer"]}
    if tipe == "entry"    : return {"type": "Entry" }
    if tipe == "buttons"  : return {"type": "Buttons", "buttons": items, "selectable": True, **({"ColumnCount": 2} if is_yesno(items) else {}) }
    if tipe == "scheduler": return {"type": "Scheduler", "days_ahead": 1, "flow": "flow://flows/sessions", "count":2, "message": "It's time to practice thinking flexibly! Head over to Mindtrails Movement for your scheduled session."}
    if tipe == "checkbox" : return {"type": "Buttons", "buttons": items, "selectable": True, "multiselect": True }
    if tipe == "timedtext": return {"type": "TimedText", "text": text,  "Duration": 15 }
    if tipe == "puzzle"   : return {
        "type": "WordPuzzle",
        "right_feedback": "Correct!",
        "wrong_feedback": "Whoops! That doesn't look right. Please wait a moment and try again.",
        "wrong_delay": 5000,
        "display_delay": 2000,
        "words": items
    }
    return None

def create_long_pages(label, scenario_description, thoughts, feelings, behaviors, image_url):
    """
    :param label: The title of the long scenario
    :param scenario_description: The text for the scenario
    :param thoughts: list of thoughts to show for long scenarios
    :param feelings: list of feelings to show for long scenarios
    :param behaviors: list of behaviors to show for long scenarios
    :return: a page group for the long scenario
    """

    pages = []
    label = label.strip()

    thoughts  = [t.strip() for t in thoughts ]
    feelings  = [f.strip() for f in feelings ]
    behaviors = [b.strip() for b in behaviors]

    with open(f"{dir_csv}/MTM_long_scenarios_structure.csv","r", encoding="utf-8") as csvfile:
        for row in islice(csv.reader(csvfile),1,None):

            input_1, is_image, timeout = lower(row[6]), lower(row[10]) == "true", row[13]

            title = row[0].replace("[Scenario_Name]", label)
            descr = clean_up_unicode(row[4].replace("[Scenario_Description]", scenario_description))

            text  = {"type": "Text", "text": descr}
            media = {"type": "Media", "url": lower(image_url), "border": True} if is_image else None

            show_buttons = "AfterTimeout" if timeout else "WhenComplete" if input_1 == "timedtext" else None

            if input_1 != "timedtext":
                timedtext = None
            elif "thoughts" in descr:
                timedtext = thoughts
            elif "feelings" in descr:
                timedtext = feelings
            elif "behaviors" in descr:
                timedtext = behaviors

            if timedtext: shuffle(timedtext,"long_pages")

            #input_1 is either timedtext or entry
            input = create_input(input_1,text=timedtext)

            pages.append({
                "header_text": title,
                "header_icon": "assets/subtitle.png",
                "elements": list(filter(None,[text,media,input])),
                **create_nav_conditions(show_buttons,timeout,[input_1])
            })

    return pages

def create_scenario_pages(domain, label, scenario_num, puzzle_text_1, word_1, comp_question,
                          answers, correct_answer, image_url, is_first, word_2=None,
                          puzzle_text_2=None, n_missing=1, include_lessons_learned=False,
                          lessons_learned_dict=None, tipe=None):

    try:
        assert correct_answer.lower() in [a.lower() for a in  answers]
    except:
        print(1)

    n_missing = lower(str(n_missing))
    pages = []

    if include_lessons_learned and domain in lessons_learned_dict:  # if it should include a "lessons learned" page
        pages.append({
            "header_text": "Lessons Learned",
            "header_icon": "assets/subtitle.png",
            "elements": [
                {"type": "Text","Text": clean_up_unicode(lessons_learned_dict[domain])},
                {"type": "Entry", "name": f"lessons_learned_{domain}_{scenario_num}"}
            ]
        })

    if n_missing == "all" and is_first:
        # if all letters missing, and it's the first scenario, add an instructions page
        pages.append({
            "header_text": "Instructions",
            "header_icon": "assets/subtitle.png",
            "elements": [{
                "type": "Text",
                "text": "The stories you're about to see are a little bit different than ones you've "
                        "seen before. Rather than fill in missing letters to complete the final word, "
                        "we're going to challenge you to generate your own final word that will complete "
                        "the story. Your goal is to think of a word that will end the story on a "
                        "positive note. The ending doesn't have to be so positive that it doesn't "
                        "seem possible, but we want you to imagine you are handling the situation well.",
            }]
        })

    pages.append({  # adding the image page
        "header_text": label,
        "header_icon": "assets/subtitle.png",
        "elements": [
            {"type": "Label", "text": label },
            {"type": "Media", "url": lower(image_url) }
        ]
    })

    pages.append({  # adding the puzzle page
        "header_text": label,
        "header_icon": "assets/subtitle.png",
        "elements": [
            {
                "type": "Text", "text": puzzle_text_1
            },
            {
                "type": "WordPuzzle",
                "name": f"{label}_{domain}_puzzle1",
                "correct_feedback": "Correct!",
                "incorrect_feedback": "Whoops! That doesn't look right. Please wait a moment and try again.",
                "incorrect_delay": 5000,
                "display_delay": 2000,
                "words": [word_1]
            }
        ],
        "navigation_conditions": "wait_for_correct"
    })

    if n_missing in ["1","2"]:
        pages[-1]["elements"][-1]["missing_letter_count"] = int(n_missing)
    elif n_missing == "all":
        pages[-1]["elements"][-1] = {"type": "Entry", "name": f"{label}_{domain}_entry1" }

    if has_value(word_2) and has_value(puzzle_text_2):
        pages.append({
            "header_text": label,
            "header_icon": "assets/subtitle.png",
            "elements": [
                {
                    "type": "Text", "text": puzzle_text_2
                },
                {
                    "type": "WordPuzzle",
                    "name": f"{label}_{domain}_puzzle_word2",
                    "correct_feedback": "Correct!",
                    "incorrect_feedback": "Whoops! That doesn't look right. Please wait a moment and try again.",
                    "incorrect_delay": 5000,
                    "display_delay": 2000,
                    "words": [word_2]
                }
            ],
            "navigation_conditions": "wait_for_correct"
        })

        if n_missing in ["1","2"]:
            pages[-1]["elements"][-1]["missing_letter_count"] = int(n_missing)
        elif n_missing == "all":
            pages[-1]["elements"][-1] = {"type": "Entry", "name": f"{label}_{domain}_entry2" }

    if n_missing != "all":
        pages.append({
            "header_text": label,
            "header_icon": "assets/subtitle.png",
            "elements": [
                {
                    "type": "Text", "Text": comp_question
                },
                {
                    "type": "Buttons",
                    "name": f"{label}_{domain}_comp_question",
                    "correct_feedback": "Correct!",
                    "incorrect_feedback": "Whoops! That doesn't look right. Please wait a moment and try again.",
                    "incorrect_delay": 5000,
                    "buttons": answers,
                    "columnCount": 1,
                    "correct_value": correct_answer
                }
            ],
            "navigation_conditions":["wait_for_correct","wait_for_click"]
        })

    for page in pages:
        if tipe: page["type"] = tipe
        page["scenario_num"] = scenario_num

    return pages

def create_resource_page(motivations, tips, ER_lookup, domain):

    resource_type = random.choice(["Motivation", "Tip", "ER Strategy"])

    if resource_type == "Motivation":
        [label,text] = motivations.pop(0)
        motivations.append([label,text])

        text = f"{label} \n\n {text}"
        title = f"Reflection"
        input  = None

    if resource_type == "Tip":
        label,text = tips.pop(0)  # pop the first list within the lists out of tip
        tips.append([label,text])  # adding that tip back to the end of the list

        title = "Apply to Daily Life: Make It Work for You!"
        input = {"type": "Entry", "name": f"{label}_entry"}

    if resource_type == "ER Strategy":
        [label,text] = ER_lookup[domain].pop(0)
        ER_lookup[domain].append([label,text])

        title = f"Manage Your Feelings: {domain}"
        input = None

    text = { "type": "Text", "text": text }
    elements = [text,input] if input else [text]

    return {"header_text": title, "header_icon": "assets/subtitle.png", "elements": elements }

def create_discrimination_page(conditions, text, items, input_1, input_name, variable_name, title):

    text = {"type": "Text", "text": text, 'html':True}
    input = create_input(input_1, items)

    if input and input_name: input["name"] = input_name
    if input and variable_name: input["variable_name"] = variable_name

    elements = [text,input] if input else [text]
    page = {
        "header_text": title,
        "header_icon": "assets/subtitle.png",
        "elements": elements,
        **create_conditions(conditions),
        **create_nav_conditions(inputs=[input_1])
    }

    return page

def create_survey_page(text=None, media=None, image_framed=None, items=None, input_1=None, input_2=None,
                       variable_name=None, title=None, input_name=None, minimum=None, maximum=None,
                       show_buttons=None, conditions=None, timeout=None):
    """
    This function creates a page with a survey question.
    :param text: Text to go on the page
    :param media: Link to image or video that should be shown on that page
    :param image_framed: True/False if the image should be framed in the middle of the page (as opposed to taking up the entire screen)
    :param items: Options for buttons, or other text options ("OtherChoices") for slider questions (usually 'Prefer not to answer')
    :param input_1:  Buttons, Picker, Checkbox, Puzzle, Entry, Slider, Scheduler
    :param input_2: Second input on the page:  Buttons, Picker, Checkbox, Puzzle, Entry, Slider, Scheduler
    :param variable_name: If later pages being shown depend on the answer to this page, you need to set a VariableName for it
    :param title: title of the page
    :param input_name: the name that will pair with the survey question when the participant's data from the app is downloaded. This is very important to have for each page that you want to save a participant's response to
    :param minimum: minimum value for sliders
    :param maximum: maximum value for sliders
    :param show_buttons: "WhenCorrect" if next button is shown only after the participant answers it correctly,
                         "AfterTimeout" if next button is shown after a certain time (timeout) has happened,
                         "Never" if the next button is never shown, &  the page will automatically go to next page after timeout
    :param conditions: conditions that need to be met to view the page. For example
                            "StressLevel; 6, 7" will be parsed to ["StressLevel", "6, 7"]
                            The first item in the list is the VariableName, the second item are the answers that need
                            to have been selected in order for teh page to appear.
                            In this case, someone has to pick "6" or "7" for the StressLevel question in order to
                            see the page
    :param timeout: see show_buttons "AfterTimeout"
    :return: a page for a survey question / text page
    """

    textinput  = {"type": "Text", "text": text} if has_value(text) else None
    mediainput = {"type": "Media", "url": lower(media), "border": lower(image_framed) == "true"} if media else None

    input1 = create_input(input_1, items, minimum, maximum)
    input2 = create_input(input_2, items, minimum, maximum)

    if lower(input_1) == "scheduler": input1["name"] = 'schedule_session'
    if lower(input_2) == "scheduler": input2["name"] = 'schedule_session'

    if input1 and input_name: input1["name"] = input_name
    if input2 and input_name: input2["name"] = input_name

    if variable_name and     input1            : input1["variable_name"] = variable_name
    if variable_name and not input1 and input2 : input2["variable_name"] = variable_name

    page     = {
        "header_text": title,
        "header_icon": "assets/subtitle.png",
        "elements": list(filter(None, [textinput, mediainput, input1, input2] )),
        **create_conditions(conditions),
        **create_nav_conditions(show_buttons,timeout,[input_1,input_2])
    }

    return page

def create_subdomain_page(subdomain, resource_texts):
    resource_text = '<br/><br/><br/><br/>'.join(resource_texts)
    return {
        "header_text": subdomain,
        "header_icon": "assets/subtitle.png",
        "elements": [ { "type": "Text", "html": True, "text": resource_text } ]
    }

def create_video_page(video_number):
    return {
        "elements": [
            {"type": "Text" , "text": "Please press play on the training video below to learn more!"},
            {"type": "Media", "url": f"/videos/video{video_number}.mp4", "border": True}
        ]
    }

def create_write_your_own_page(text, input_1, title, input_name):
    page = create_survey_page(text=text, input_1=input_1, title=title, input_name=input_name)
    page["header_text"] = title or "Write Your Own"
    page["header_icon"] = "assets/subtitle.png",
    return page
