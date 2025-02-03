import csv
import shutil
import json

from collections import defaultdict
from itertools import islice, chain, product
from pathlib import Path

from helpers_pages import create_scenario_pages, create_survey_page, create_video_page
from helpers_utilities import clean_up_unicode, create_puzzle, get_groupnames, shuffle

dir_root = "./make"
dir_csv  = f"{dir_root}/CSV"
dir_out  = f"{dir_root}/~out"

Path(dir_out).mkdir(parents=True,exist_ok=True)

def get_relflows(groupname):
    return f"{groupname}"

def get_relpages(groupname,flowname):
    return f"{groupname}/{flowname}"

def get_flownames():
    yield 'intro'
    yield 'biweekly_2'
    yield 'biweekly_4'
    yield 'biweekly_6'
    yield 'biweekly_10'
    yield 'eod'
    yield 'reasons for ending'

def get_flowpages(flow_name,pop_name,group_name,survey_pages):

    # This part gets a little messy and has to be hard coded
    # All the possible options we care about are below

    # 1,PD_Dose
    # 1,PD_Control_Dose
    #
    # All,PD_EOD
    # All,PD_BeforeDomain
    # All,PD_AfterDomain
    #
    # All,PD_Biweekly
    # All,PD_Biweekly_Control
    #
    # Week 2,PD_Biweekly
    # Week 4,PD_Biweekly
    # Week 6,PD_Biweekly
    # Week 10,PD_Biweekly
    #
    # All,PD_ReasonsforEnding
    # All,PD_ReasonsforEnding_Control
    #
    # ------------------------------------
    #
    # 1,HD_Dose
    # 1,HD_Control_Dose
    #
    # All,HD_EOD
    # All,HD_BeforeDomain
    # All,HD_AfterDomain
    #
    # All,HD_Biweekly
    # All,HD_Biweekly_Control
    #
    # Week 2,HD_Biweekly
    # Week 4,HD_Biweekly
    # Week 6,HD_Biweekly
    # Week 10,HD_Biweekly
    #
    # All,HD_ReasonsforEnding
    # All,HD_ReasonsforEnding_Control

    pop_name = pop_name.lower()
    flat = chain.from_iterable

    if flow_name == "intro" and group_name == "treatment":
        yield from flat(survey_pages[("1",f"{pop_name}_dose")].values())
        return

    if flow_name == "intro" and group_name == "control":
        yield from flat(survey_pages[("1",f"{pop_name}_control_dose")].values())
        return

    if flow_name == "eod" and group_name == "treatment":
        yield from flat(survey_pages[("all",f"{pop_name}_eod")].values())
        return

    if flow_name == "reasons for ending" and group_name == "treatment":
        yield from flat(survey_pages[("all",f"{pop_name}_reasonsforending")].values())
        return
    
    if flow_name == "reasons for ending" and group_name == "control":
        yield from flat(survey_pages[("all",f"{pop_name}_reasonsforending_control")].values())
        return

    if flow_name.startswith("biweekly") and group_name == "treatment":
        yield from flat(survey_pages[("all",f"{pop_name}_biweekly")].values())
        yield from flat(survey_pages[(f"weekly {flow_name.split('_')[1]}",f"{pop_name}_biweekly")].values())
        return

    if flow_name.startswith("biweekly") and group_name == "control":
        yield from flat(survey_pages[("all",f"{pop_name}_biweekly_control")].values())

def _create_practice_pages(i):
    with open(f"{dir_csv}/MTM dose1.csv", "r", encoding="utf-8") as dose1_read_obj:  # scenarios for first dose in file
        dose1_scenario_num = 0
        for row_1 in islice(csv.reader(dose1_read_obj),1,None):

            # First, add the video that goes before each scenario
            yield create_video_page(dose1_scenario_num+1)

            domain, label = row_1[0].strip(), row_1[3]
            puzzle1,puzzle2 = map(create_puzzle,row_1[i:i+2])
            question, choices, answer = row_1[i+2], row_1[i+3:i+5], row_1[i+3]

            shuffle(choices)

            # Create scenario page group for the practice
            yield from create_scenario_pages(domain=domain, label=label, scenario_num=dose1_scenario_num,
                                                    puzzle_text_1=puzzle1[0], word_1=puzzle1[1],
                                                    comp_question=question, answers=choices,
                                                    correct_answer=answer, word_2=puzzle2[1],
                                                    puzzle_text_2=puzzle2[0], unique_image=False,
                                                    row_num=dose1_scenario_num)

            if dose1_scenario_num == 0:
                make_it_your_own_text = ("We want Mindtrails Movement to meet your needs. When you complete "
                                        "training sessions in the app or browse resources in the "
                                        "on-demand resource library, you'll notice a button that looks "
                                        "like a star on the top right-hand corner of your screen. By "
                                        "clicking on the star, you can add the info you find most " 
                                        "helpful (e.g., short stories, tips for managing stress) to your "
                                        "own personal Favorites page. You can then revisit your favorite "
                                        "parts of the app whenever you'd like by choosing the Favorites " 
                                        "tile from the Mindtrails Movement homepage!")

                page = create_survey_page(text=make_it_your_own_text, title="Make it your own!")

                yield page

            dose1_scenario_num += 1

def _create_survey_page(row):
    text = clean_up_unicode(row[4])

    title = row[1].strip()
    input_1 = row[5]
    input_2 = row[6]
    minimum = row[7]
    maximum = row[8]
    media = row[9]
    items = row[10]
    image_framed = row[11]
    timeout = row[12]
    show_buttons = row[13]
    variable_name = row[16]
    conditions = row[17].split('; ')
    input_name = row[18]

    return create_survey_page(conditions=conditions, text=text,
                                show_buttons=show_buttons, media=media, image_framed=image_framed,
                                items=items, input_1=input_1, input_2=input_2,
                                variable_name=variable_name, title=title, input_name=input_name,
                                minimum=minimum, maximum=maximum, timeout=timeout)

# The keys in this dictionary correspond to the HTC_survey_questions.csv lookup codes (<Doses>,<Subject>)
# You can see all the lookup codes and their meanings below:
# https://docs.google.com/spreadsheets/d/1Z_syG-HbyFT2oqMsHnAbidRtlH97IVxnBqbNKZWbwLY/edit#gid=0

survey_pages = defaultdict(lambda: defaultdict(list))

populations = [
    ["HD", 4 ], # dose 1 scenarios index
    ["PD", 10]  # dose 1 scenarios index
]

for (pop_name, d) in populations:

    #Read the survey questions
    with open(f"{dir_csv}/MTM_survey_questions - Final_{pop_name} MTM_survey_questions.csv", "r", encoding="utf-8") as read_obj:

        for row in islice(csv.reader(read_obj),1,None):

            # In *survey_questions.csv each row is a single question (aka, "page") in Digital Trails.
            # The "Subject" column indicates which script/flow type the question belongs to and the
            # "Dose" column indicates which run of the "Subject" flow the row belongs too.

            # One counter-intuitve aspect of this is the "Introduction" survey. This flow has a subject
            # of "Dose" (i.e., the same as the session microdoses). This is because the Intro flow is
            # a special flow that only occurs on the first microdose session. Therefore, intro flow
            # questions are all rows in *survey_questions.csv with Subject=Dose and Dose=1.

            # Each flow can be uniquely identified by the flow it
            # belongs to and which run of that flow it appears on

            dose        = row[2].lower()
            subject     = row[3].lower()
            group_id    = (dose,subject)
            subgroup_id = row[0]

            if row[0] == "Práctica CBM-I":
                survey_pages[group_id][subgroup_id].extend(_create_practice_pages(d))
            elif row[2]:
                survey_pages[group_id][subgroup_id].append(_create_survey_page(row))

    #Create the surveys
    for group_name,flow_name in product(get_groupnames(),get_flownames()):

        root_dir = f"{dir_out}/{pop_name}/{group_name}"
        pages_dir = f"{root_dir}/biweekly/{int(flow_name[-1])//2}" if "biweekly" in flow_name else f"{root_dir}/{flow_name}"

        shutil.rmtree(pages_dir,ignore_errors=True)

        Path(pages_dir).mkdir(parents=True,exist_ok=True)
        for i,page in enumerate(get_flowpages(flow_name, pop_name, group_name, survey_pages),1):
            with open(f"{pages_dir}/{i}.json", 'w', encoding='utf-8') as f:
                json.dump(page, f, indent=4, ensure_ascii=False)

    #Configure biweekly so they only get one survey at a time
    for group_name in get_groupnames():
        biweekly_config_path = f"{dir_out}/{pop_name}/{group_name}/biweekly/__flow__.json"
        biweekly_config_json = {"mode":"sequential","size":1}
        with open(biweekly_config_path, 'w', encoding='utf-8') as f:
            json.dump(biweekly_config_json, f, indent=4, ensure_ascii=False)
