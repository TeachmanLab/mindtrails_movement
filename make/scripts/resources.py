import shutil
import csv

from itertools import islice
from collections import defaultdict
from pathlib import Path

from helpers_pages import create_subdomain_page
from helpers_utilities import dir_safe, get_groupnames, write_output

dir_root = "./make"
dir_csv  = f"{dir_root}/CSV"
dir_out  = f"{dir_root}/~out"

Path(dir_out).mkdir(parents=True,exist_ok=True)

def resource_domain_selection_text():
    return ("Please click on any topic to learn about resources that "
            "can help you manage that part of your life.\n\nThough "
            "resources were carefully selected by our team of researchers "
            "and clinicians, the University of Virginia does not endorse "
            "these resources.")

def resource_subdomain_selection_text():
    return ("Click on the specific topic to see associated resources.")

def resource_text(resource_name, resource_link, resource_text):
    return f"""<b><font color="#9769ED" size=6>{resource_name}</font></b>
               <br/><br/>{resource_text}<br/><br/>
               <a href="{resource_link}">{resource_link}</a>"""

for popname in ["HD","PD"]:

    domains = defaultdict(lambda:defaultdict(list))

    # Read the resources
    with open(f"{dir_csv}/MT Movement Resources for On-Demand Library - {popname} Resources.csv", "r", encoding="utf-8") as read_obj:
        for row in islice(csv.reader(read_obj), 1, None):
            domain,subdomain,res_name,res_link,res_text = row
            domains[domain][subdomain].append(resource_text(res_name,res_link,res_text))

    # Define folders
    folders = {'__flow__.json': {"mode":"select", "column_count": 2, "title_case": True, "text":resource_domain_selection_text()}}
    for domain, subdomains in domains.items():
        folders[f"{dir_safe(domain)}/__flow__.json"] = {"mode":"select", "text":resource_subdomain_selection_text(), "last_item": "other"}
        for subdomain, resources in subdomains.items():
            folders[f"{dir_safe(domain)}/{dir_safe(subdomain)}.json"] = create_subdomain_page(subdomain,resources)

    # Delete old JSON
    for groupname in get_groupnames():
        shutil.rmtree(f"{dir_out}/{popname}/{groupname}/resources", ignore_errors=True)

    # Write new JSON
    for groupname in get_groupnames():
        write_output(f"{dir_out}/{popname}/{groupname}/resources", folders)