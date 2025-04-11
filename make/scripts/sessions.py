import csv
import shutil

from collections import defaultdict
from itertools import islice, cycle, chain
from pathlib import Path

from helpers_pages import create_discrimination_page, create_scenario_pages, create_survey_page,create_resource_page
from helpers_pages import create_long_pages, create_write_your_own_page, create_video_page
from helpers_utilities import get_motivations, get_ER, get_tips, clean_up_unicode, has_value, create_puzzle, dir_safe, shuffle, write_output

dir_root = "./make"
dir_csv    = f"{dir_root}/CSV"
dir_out    = f"{dir_root}/~out"
dir_flows  = f"{dir_out}/treatment"
dir_doses  = f"{dir_flows}/doses"
dir_before = f"{dir_doses}/__before__"
dir_after  = f"{dir_doses}/__after__"
dir_after  = f"{dir_doses}/__first__"

Path(dir_out).mkdir(parents=True,exist_ok=True)

def flat(dictionary, key):
    return list(chain.from_iterable(dictionary[key.lower()].values()))

def _create_practice_pages(i):
    with open(f"{dir_csv}/MTM dose1_scenarios.csv", "r", encoding="utf-8") as dose1_read_obj:  # scenarios for first dose in file
        dose1_scenario_num = 0
        for row_1 in islice(csv.reader(dose1_read_obj),1,None):

            # First, add the video that goes before each scenario
            yield create_video_page(dose1_scenario_num+1)

            domain, label = row_1[0].strip(), row_1[3]
            puzzle1,puzzle2 = map(create_puzzle,row_1[i:i+2])
            question, choices, answer = row_1[i+2], row_1[i+3:i+5], row_1[i+3]
            image_url = row_1[9]

            shuffle(choices)

            # Create scenario page group for the practice
            yield from create_scenario_pages(domain=domain, label=label, scenario_num=dose1_scenario_num,
                                                    puzzle_text_1=puzzle1[0], word_1=puzzle1[1],
                                                    comp_question=question, answers=choices,
                                                    correct_answer=answer, word_2=puzzle2[1],
                                                    puzzle_text_2=puzzle2[0], image_url=image_url,
                                                    row_num=dose1_scenario_num)

            if dose1_scenario_num == 0:
                make_it_your_own_text = ("We want Mindtrails Movement to meet your needs. When you "
                                         "complete training sessions in the app or browse resources in "
                                         "the on-demand resource library, you'll notice a button that "
                                         "looks like a star on the top right-hand corner of your screen. "
                                         "By clicking on the star, you can add the info you find most "
                                         "helpful (e.g., short stories, tips for managing stress) to "
                                         "your own personal Favorites page. You can then revisit your "
                                         "favorite parts of the app whenever you'd like by choosing "
                                         "the Favorites tile from the Mindtrails Movement homepage!")

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
                              show_buttons=show_buttons, media=media,
                              image_framed=image_framed, items=items,
                              input_1=input_1, input_2=input_2,
                              variable_name=variable_name, title=title,
                              input_name=input_name, minimum=minimum,
                              maximum=maximum, timeout=timeout)

def domain_selection_text():
    return (
        "The domains listed here are some areas that may cause you to feel anxious. " 
        "Please select the one that you'd like to work on during today's training."
        "\n\nWe encourage you to choose different domains to practice thinking "
        "flexibly across areas of your life!"
    )

def create_lessons_learned(popname):
    with open(f"{dir_csv}/MTM lessons_learned_text - {popname}.csv", 'r', encoding='utf-8') as read_obj:
        return { row[0]:row[1] for row in islice(csv.reader(read_obj),1,None) }

def create_long_doses(popname,i):
    long_doses = defaultdict(list)

    with open(f"{dir_csv}/MT Movement Final Long Scenarios - MTM Long Scenarios-{popname} FOR APP.csv", "r",encoding="utf-8") as read_file:
        for row in islice(csv.reader(read_file),2,None):

            if not row: continue # Skip empty lines

            if len(row) > max(i + 16, 3):  # Ensure the row has enough columns
                domain_1 = row[0].strip()
                domain_2 = row[1].strip() if row[1] else None
                label = row[3]
                image_url = row[5]
                scenario_description = row[i]
                thoughts = row[i+2:i+7]
                feelings = row[i+7:i+12]
                behaviors = row[i+12:i+17]
                
                if not has_value(scenario_description) or not has_value(label): continue

                dose = create_long_pages(label=label, scenario_description=scenario_description,
                                        thoughts=thoughts, feelings=feelings, behaviors=behaviors, 
                                        image_url=image_url)
                # add page group to correct domain's list
                long_doses[domain_1].append(dose)
                # if it also belongs to a second domain, add the page group to that list
                if domain_2: long_doses[domain_2].append(dose)

    # shuffle each list of long scenario page groups
    for domain in long_doses: shuffle(long_doses[domain])

    return {k:iter(cycle(v)) for k,v in long_doses.items()}

def create_short_doses(popname,i):
    short_doses   = defaultdict(list)
    domain_rindex = defaultdict(int)
    domain_ndoses = defaultdict(int)

    lessons_learned_dict = create_lessons_learned(popname)

    with open(f"{dir_csv}/MTM Short Scenarios by Session - Initial Protocol {popname}.csv","r", encoding="utf-8", newline='') as read_obj:

        for row in islice(csv.reader(read_obj),1,None):
            domain_1  = row[0].strip() #Broad domain 1
            label     = row[3]  # scenario name, Hoos TC title column
            image_url = row[9]

            if not domain_1 or not label: continue

            if "Write Your Own" in label:
                # Add a place holder that will be replaced with
                # a write your own dose in final processing
                short_doses[domain_1].append("Write Your Own")
                domain_ndoses[domain_1] += 10 #bump the dose count by 10 (because the dose size of a long scenario = 10)
                continue

            puzzle1,puzzle2 = map(create_puzzle,row[i:i+2])

            if puzzle1 == (None,None): continue

            comp_question, choices, answer  = row[i+2], row[i+3:i+5], row[i+3]

            if choices[0].strip().lower() in ['yes','no']: choices = ["Yes","No"]

            shuffle(choices)

            if row[10]: letters_missing = row[10]

            # Every 40 doses we want to show them lessons learned.
            # This doesn't account for long scenarios or write your own
            lessons_learned = domain_ndoses[domain_1] and domain_ndoses[domain_1] % 40 == 0

            if lessons_learned and domain_1 not in lessons_learned_dict:
                print(f"{domain} not in {popname} lessons learned")

            dose = create_scenario_pages(domain=domain_1, label=label, scenario_num=domain_rindex[domain_1],
                                         puzzle_text_1=puzzle1[0], word_1=puzzle1[1],
                                         comp_question=comp_question, answers=choices,
                                         correct_answer=answer, word_2=puzzle2[1],
                                         puzzle_text_2=puzzle2[0],
                                         letters_missing=letters_missing,
                                         lessons_learned=lessons_learned,
                                         lessons_learned_dict=lessons_learned_dict,
                                         row_num=domain_ndoses[domain_1],
                                         image_url=image_url)

            domain_rindex[domain_1] += 1
            domain_ndoses[domain_1] += 1

            short_doses[domain_1].append(dose)

    return short_doses

def create_surveys(popname,i):
    accepted = [f"{popname}_beforedomain_all", f"{popname}_afterdomain_all", f"{popname}_dose_1", f"{popname}_control_dose_1"]
    accepted = [a.lower() for a in accepted]
    surveys  = defaultdict(lambda:defaultdict(list))

    # Open the file with all the content
    with open(f"{dir_csv}/MTM_survey_questions - Final_{popname} MTM_survey_questions.csv", "r", encoding="utf-8") as read_obj:
        for row in islice(csv.reader(read_obj),1,None):
            lookup_id, subgroup_id = f"{row[3]}_{row[2]}".lower(), row[0]

            if lookup_id not in accepted:
                continue
            elif row[0] == "Practice CBM-I":
                surveys[lookup_id][subgroup_id].extend(_create_practice_pages(i))
            elif row[2]:
                surveys[lookup_id][subgroup_id].append(_create_survey_page(row))

    return surveys

def create_write_your_own_dose():
    pages = []
    with open(f"{dir_csv}/MTM_write_your_own.csv", "r", encoding="utf-8") as f:
        for row in islice(csv.reader(f),1,None):
            text = clean_up_unicode(row[4])
            if text:
                title = row[1]
                input_1 = row[5]
                input_name = row[18]
                pages.append(create_write_your_own_page(text, input_1, title, input_name))
    return pages

def create_resource_dose_creator(popname):
    regulation  = get_ER(file_path=f"{dir_csv}/MT Movement Ranked Statements and Tips (post-session recommendations) - ER Strategies- {popname}.csv")
    tips        = get_tips(file_path=f"{dir_csv}/MT Movement Ranked Statements and Tips (post-session recommendations) - Tips to Apply Lessons Learned.csv")
    motivations = get_motivations(file_path=f"{dir_csv}/MT Movement Ranked Statements and Tips (post-session recommendations) - New {popname} Motivational Statements.csv")

    return lambda domain: [create_resource_page(motivations, tips, regulation, domain)]

def create_discrimination_dose(popname):
    pages = []
    with open(f"{dir_csv}/MTM Discrimination - MTM ({popname}).csv", "r", encoding="utf-8") as f:
        for row in islice(csv.reader(f),1,None):
            title, text, input_1, input_name = row[0], row[1], row[2], row[15]
            items, conditions = row[7], row[14].split('; ')

            pages.append(create_discrimination_page(conditions=conditions,
                                                    text=text,
                                                    items=items,
                                                    input_1=input_1,
                                                    input_name=input_name,
                                                    title=title))
    return pages

populations = [
    ["HD", 4, 4, 4 ], #short scenario index, long scenario index, dose 1 scenarios index
    ["PD", 4, 4, 10]
]

for popname,s,l,i in populations:

    surveys      = create_surveys(popname,i)
    short_doses  = create_short_doses(popname,s)             # dict of doses by domain
    long_doses   = create_long_doses(popname,l)              # dict of dose cycle by domain
    wyo_dose     = create_write_your_own_dose()      # one dose used over and over again
    resources    = create_resource_dose_creator(popname)    # lambda that takes a domain and returns a dose
    discrim_dose = create_discrimination_dose(popname) # one dose used over and over again

    domains      = short_doses.keys()
    domain_doses = defaultdict(list)

    # Create doses
    for domain in domains:
        dose_count = 1
        for short_dose in short_doses[domain]:

            if short_dose == "Write Your Own":
                dose_count += 10 #bump the row by 10 (because the dose size of a long scenario = 10)
                domain_doses[domain].append(wyo_dose)
                domain_doses[domain].append(resources(domain))
                continue

            domain_doses[domain].append(short_dose)

            if dose_count % 10 == 0:
                domain_doses[domain].append(resources(domain))

            if dose_count % 50 == 0:
                domain_doses[domain].append(next(long_doses[domain]))
                domain_doses[domain].append(resources(domain))

            dose_count += 1

    # Define folders
    folders = {}
    folders['control/sessions/__first__'] = flat(surveys,f"{popname}_control_dose_1")
    folders['treatment/sessions/__flow__.json'] = {"mode":"select", "title_case": True, "column_count":2, "text": domain_selection_text(), "title":"MindTrails Movement"}
    folders['treatment/sessions/__first__'] = flat(surveys,f"{popname}_dose_1")
    folders['treatment/sessions/__before__'] = flat(surveys,f"{popname}_beforedomain_all")
    folders['treatment/sessions/__after__'] = flat(surveys,f"{popname}_afterdomain_all")
    folders['treatment/sessions/Discrimination'] = discrim_dose
    for domain, doses in domain_doses.items():
        folders[f'treatment/sessions/{dir_safe(domain)}/__flow__.json'] ={"mode":"sequential", "take":1, "repeat":True}
        for i, dose in enumerate(doses,1):
            folders[f'treatment/sessions/{dir_safe(domain)}/{i}'] = dose

    # Delete old JSON
    shutil.rmtree(f"{dir_out}/{popname}/control/sessions",ignore_errors=True)
    shutil.rmtree(f"{dir_out}/{popname}/treatment/sessions",ignore_errors=True)

    # Write new JSON
    write_output(f"{dir_out}/{popname}", folders)
