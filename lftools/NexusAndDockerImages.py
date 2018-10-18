#!/usr/bin/python3

import logging
import sys
import os
import argparse
import requests
import re
import docker
#import subprocess
import time
import datetime
import multiprocessing
from multiprocessing.dummy import Pool as ThreadPool
from tqdm import tqdm
import socket
import requests
import urllib3

## Workflow if you do it manually
##    docker pull nexus3.onap.org:10002/onap/aaf/aaf_hello:2.1.3
##    docker images --> imageid --> 991170554e6e
##    docker tag 991170554e6e onap/aaf-aaf_hello:2.1.3
##    docker push onap/aaf-aaf_hello:2.1.3
##    docker image rm --force 991170554e6e

NEXUS3_BASE="https://nexus3.onap.org:10002/"
NEXUS3_CATALOG=NEXUS3_BASE + "v2/_catalog"

##
## Filter
## Find all projects that starts with MAIN_PART and contains FindProject.
##
## Set MAIN_PART to the common beginning of the project name.
## MAIN_PART = onap --> find all projects starting with onap
MAIN_PART   = "onap"
## Set the FindProject to "" to find all projects that starts with MAIN_PART
## Set the FindProject to a str to find all projects that contains that string
##  and starts with MAIN_PART
FindProject = "aaf_co"   # onap/aaf/aaf_config,onap/aaf/aaf_core
#FindProject = "aaf_cm"   # onap/aaf/aaf_cm
FindProject = "aa"
#FindProject = ""        # Find all projects

ExecuteCopy=False

TRACE_LEVEL=logging.INFO

NexusCatalog = []
NEXUS3_PROJ_NAME_HEADER = "Nexus3 Project Name"
DOCKER_PROJ_NAME_HEADER = "Docker Project Name"
## Set project_max_len_chars to the max len of the headers, for pretty printouts.
project_max_len_chars = max(len(NEXUS3_PROJ_NAME_HEADER),len(DOCKER_PROJ_NAME_HEADER))
TotTagsToBeCopied = 0
projects = []

def _format_nexus_url(url):
    # Need to remove https:// from the NEXUS3_BASE if its there.
    if url.startswith('https://'):
        return url[len('https://'):]
    else:
        return url

def _format_image_id(id):
    if id.startswith("sha256:"):
        return id[len('sha256:'):]
    else:
        return id


class TagClass:
    def __init__(self ):
        self.valid = []
        self.invalid = []
        self.repository_exist = True

    ## x.y.z-KEYWORD-yyyymmddThhmmssZ   where keyword = STAGING or SNAPSHOT
    ## 1.1.2-SNAPSHOT-20181231T234559Z
    ##  pattern = re.compile(r'^\d+.\d+.\d+-(STAGING|SNAPSHOT)-(20\d{2})(\d{2})(\d{2})T([01]\d|2[0-3])([0-5]\d)([0-5]\d)Z$')
    #pattern = re.compile(r'^\d+$|^\d+.\d+$|^\d+.\d+.\d+$')
    def validate_tag(self, check_tag):
        pattern = re.compile(r'^\d+.\d+.\d+$')
        logger.debug ("validate tag %s --> %s" % (check_tag, pattern.match(check_tag)))
        return pattern.match(check_tag)

    def add_tag (self, new_tag):
        if self.validate_tag(new_tag):
            self.valid.append(new_tag)
        else:
            self.invalid.append(new_tag)

class NexusTagClass (TagClass):
    def __init__(self, NexusProject):
        TagClass.__init__(self)
        logger.debug ("Fetching nexus tags for %s" % (NexusProject))
        r = requests.get (NEXUS3_BASE + "v2/" + NexusProject + "/tags/list")
        # {"name":"onap/aaf/aaf_service","tags":["2.1.1","2.1.3","2.1.4","2.1.5"]}
        logger.debug ( "r.status_code = %d, ok=%s" % (r.status_code, r.status_code == requests.codes.ok))
        if r.status_code == requests.codes.ok:
            raw_tags  = r.text
            raw_tags  = raw_tags.replace ('"', '')
            raw_tags  = raw_tags.replace ('}', '')
            raw_tags  = raw_tags.replace (']', '')
            raw_tags  = raw_tags.split   ('[')
            TmpSplittedTags   = raw_tags[1].split(',')
            if len(TmpSplittedTags)>0:
                for tag_2_add in TmpSplittedTags:
                    self.add_tag(tag_2_add)
                    logger.debug ("Nexus %s has tag %s" % (NexusProject, tag_2_add))
        else:
            self.repository_exist = False

## curl -s https://registry.hub.docker.com/v1/repositories/onap/base_sdc-sanity/tags|
## [{"layer": "", "name": "latest"}, {"layer": "", "name": "v1.0.0"}]
class DockerTagClass (TagClass):
    DOCKER_BASE="https://registry.hub.docker.com/v1/repositories"
    def __init__(self, DockerProject):
        TagClass.__init__(self)
        logger.debug ("Fetching docker tags for %s" % (DockerProject))
        r = requests.get (self.DOCKER_BASE + "/" + DockerProject + "/tags")
        logger.debug ( "r.status_code = %d, ok=%s" % (r.status_code, r.status_code == requests.codes.ok))
        if r.status_code == requests.codes.ok:
            raw_tags  = r.text
            raw_tags  = raw_tags.replace ('}]', '')
            raw_tags  = raw_tags.replace ('[{', '')
            raw_tags  = raw_tags.replace ('{', '')
            raw_tags  = raw_tags.replace ('"', '')
            TmpSplittedTuple  = raw_tags.split ('}')
            if len(TmpSplittedTuple)>0:
                for tuple in TmpSplittedTuple:
                    tmp_tuple = tuple.split(':')
                    if len(tmp_tuple)>1:
                        self.add_tag(tmp_tuple[2].strip())
                        logger.debug ("Docker %s has tag %s" % (DockerProject, tmp_tuple[2]))
        else:
            self.repository_exist = False

class ProjectClass:
    nexus_project_name = ""
    docker_project_name = ""

    def __init__(self, nexus_proj):
        self.set_nexus_project_name  (nexus_proj)
        self.set_docker_project_name (nexus_proj)
        self.nexus_tags = NexusTagClass (self.nexus_project_name)
        self.docker_tags = DockerTagClass (self.docker_project_name)
        self.tags_2_copy = TagClass ()
        self.populate_tags_to_copy()
        self.docker_client = docker.from_env()

    def __lt__(self, other):
        return self.nexus_project_name < other.nexus_project_name

    def set_nexus_project_name (self, proj_name):
        self.nexus_project_name = proj_name

    def set_docker_project_name (self, proj_name):
        # Remove ${MAIN_PART}/    for instance onap/
        if (len(MAIN_PART) > 0):
            tmp_main_part=MAIN_PART + "/"
        else
            tmp_main_part=""
        if proj_name.startswith(tmp_main_part):
            docker_name=proj_name[len(tmp_main_part):]
        else:
            docker_name=proj_name
        # Change / --> -
        docker_name  = docker_name.replace ('/', '-')
        # Add main part to beginning
        if (len(MAIN_PART) > 0):
            docker_name  = MAIN_PART + "/" + docker_name
        self.docker_project_name = docker_name
        logger.debug ("ProjName = %s ---> Docker name = %s" % (proj_name, docker_name))

    ## Loop through each Nexus Tag, and check if it exists among Docker Tags
    ## Return True if it do not exist.
    def populate_tags_to_copy(self):
        if len(self.nexus_tags.valid)>0:
            for nexustag in self.nexus_tags.valid:
                if not nexustag in self.docker_tags.valid:
                    self.tags_2_copy.add_tag(nexustag)

    def _pull_tag_push_msg(self, info_text, count, retry_text = ''):
        due_to_txt = ''
        if len(retry_text) > 0:
            due_to_txt ='due to {}'.format(retry_text)

        b4_txt_template ='Attempt {}: '
        b4_txt = ''.ljust(len(b4_txt_template)-1)
        if count > 1:
            b4_txt = b4_txt_template.format(count)
        logger.info ("{}: {} {}".format(b4_txt, info_text, due_to_txt))


    def _docker_pull (self, nexus_image_str, count, tag, retry_text = ''):
        self._pull_tag_push_msg ('Pulling   nexus  image {} with tag {}'.format(self.nexus_project_name, tag), count, retry_text)
        image = self.docker_client.images.pull (nexus_image_str)
        return image

    def _docker_tag (self, count, image, tag, retry_text = ''):
        self._pull_tag_push_msg ('Creating  docker image {} with tag {}'.format(self.docker_project_name, tag), count, retry_text)
        image.tag (self.docker_project_name, tag=tag)

    def _docker_push (self, count, image, tag, retry_text):
        self._pull_tag_push_msg ('Pushing   docker image {} with tag {}'.format(self.docker_project_name, tag), count, retry_text)
        output_lines=self.docker_client.images.push (self.docker_project_name, tag=tag)

    def _docker_cleanup (self, count, image, tag, retry_text = ''):
        image_id = _format_image_id(image.short_id)
        self._pull_tag_push_msg ('Cleanup   docker image {} with tag {} and id {}'.format(self.docker_project_name, tag, image_id), count, retry_text)
        self.docker_client.images.remove (image.id, force=True)


    def docker_pull_tag_push(self):

        if len(self.tags_2_copy.valid) == 0:
            return

        for tag in self.tags_2_copy.valid:
            org_path = _format_nexus_url(NEXUS3_BASE)
            nexus_image_str = '%s%s:%s' % (org_path, self.nexus_project_name, tag)
            logger.debug ("Nexus Image Str = %s" % (nexus_image_str))
            for stage in ['pull', 'tag', 'push', 'cleanup']:
                cnt_break_loop = 1
                retry_text=''
                while (True):
                    try:
                        if stage == 'pull':
                            image = self._docker_pull(nexus_image_str, cnt_break_loop, tag, retry_text)
                            break

                        if stage == 'tag':
                            self._docker_tag (cnt_break_loop, image, tag, retry_text)
                            break

                        if stage == 'push':
                            self._docker_push (cnt_break_loop, image, tag, retry_text)
                            break

                        if stage == 'cleanup':
                            self._docker_cleanup (cnt_break_loop, image, tag, retry_text)
                            break
                    except socket.timeout:
                        retry_text='Socket Timeout'
                    except requests.exceptions.ConnectionError:
                        retry_text='Connection Error'
                    except urllib3.exceptions.ReadTimeoutError:
                        retry_text='Read Timeout Error'
                    except:
                        retry_text="Unexpected error. {}".format(sys.exc_info()[0])
                    cnt_break_loop = cnt_break_loop + 1
                    if (cnt_break_loop >= 10):
                        raise HTTPError(retry_text)

def get_nexus3_catalog():
    global NexusCatalog
    global project_max_len_chars
    project_max_len_chars = 0
    r = requests.get (NEXUS3_CATALOG)
    ## "repositories":["dcae_dmaapbc","onap/aaf/aaf-base-openssl_1.1.0","onap/aaf/aaf-base-xenial",
    logger.debug ( "r.status_code = %d, ok=%s" % (r.status_code, r.status_code == requests.codes.ok))
    if r.status_code == requests.codes.ok:
        raw_catalog  = r.text
        raw_catalog  = raw_catalog.replace ('"', '')
        raw_catalog  = raw_catalog.replace (' ', '')
        raw_catalog  = raw_catalog.replace ('}', '')
        raw_catalog  = raw_catalog.replace ('[', '')
        raw_catalog  = raw_catalog.replace (']', '')
        raw_catalog  = raw_catalog.split (':')
        TmpCatalog   = raw_catalog[1].split(',')
        for word in TmpCatalog:
            # Remove all projects that do not start with MAIN_PART
            if word.startswith (MAIN_PART):
                # If  a specific search string has been specified, search for it
                # Empty string will match all words
                if word.find (FindProject) >= 0:
                    NexusCatalog.append (word)
                    logger.debug (" Added project %s to my list" % word)
                    if len(word) > project_max_len_chars:
                        project_max_len_chars=len(word)
        logger.debug ("# TmpCatalog %d, NexusCatalog %d, DIFF = %d " % (len(TmpCatalog), len(NexusCatalog), len(TmpCatalog)-len(NexusCatalog)))


def create_docker_hub_repo(proj):
#orgname, reponame, summary=None, description=None, private=False):
    url = 'https://registry.hub.docker.com/v2'

    def bool2str(b):
       if b:
          return 'true'
       return 'false'

    if proj.docker_tags.repository_exist:
        return

    orgname = proj.docker_project_name.split('/')[0]
    reponame = proj.docker_project_name[len(orgname)+1:]
    payload = {
        'description': '',
        'full_description': '',
        'is_private': bool2str(False),
        'name': reponame,
        'namespace': orgname
    }
    logger.info("Creating missing docker project {}".format(payload))
    # How to authenticate???
    # def auth(self, username=None, password=None):
    #     url = 'https://hub.docker.com/v2/users/login'
    #     args = {
    #         'username': username,
    #         'password': password,
    #     }
    #     resp = requests.post(url, data=args)
    #     json = resp.json()
    #     if 'token' in json:
    #         self.headers['Authorization'] = 'JWT ' + json['token']
    #         return True
    #     return False

#    resp = requests.post(
#        url + '/repositories/',
#        data=payload,
#        headers={}
#    )
#    if not resp.status_code == requests.codes.ok:
#        resp.raise_for_status()
    pbar.update(1)


def create_missing_docker_projects():
    missing_docker_proj = 0
    for proj in projects:
        if not proj.docker_tags.repository_exist:
            missing_docker_proj = missing_docker_proj + 1
    if missing_docker_proj == 0:
        return

    logger.info("Creating {} missing projects in Docker".format(missing_docker_proj))

    pbar = tqdm(total=missing_docker_proj)
    pool = ThreadPool(multiprocessing.cpu_count())
    pool.map(create_docker_hub_repo, projects)
    pool.close()
    pool.join()
    pbar.close()


def _docker_pull_tag_push(proj):
    proj.docker_pull_tag_push()
    pbar.update(len(proj.tags_2_copy.valid))

def copy_from_nexus_to_docker():
    _tot_tags=0
    for proj in projects:
        _tot_tags = _tot_tags + len(proj.tags_2_copy.valid)
    pbar = tqdm(total=_tot_tags)
    pool = ThreadPool(multiprocessing.cpu_count())
    pool.map(_docker_pull_tag_push, projects)
    pool.close()
    pool.join()
    pbar.close()

def print_nexus_docker_proj_names():
    fmt_str='{:<'+str(project_max_len_chars)+'} : '
    print("")
    print (fmt_str.format(NEXUS3_PROJ_NAME_HEADER), end='')
    print (DOCKER_PROJ_NAME_HEADER)
    print ('-'*project_max_len_chars*2)
    docker_i=0
    for proj in projects:
        print (fmt_str.format(proj.nexus_project_name), end='')
        print (proj.docker_project_name)
        docker_i=docker_i+1
    print("")

def print_tags_header (header_str, col_1_str):
    fmt_str='{:<'+str(project_max_len_chars)+'} : '
    print (header_str)
    print (fmt_str.format(col_1_str), end='')
    print ('Tags')
    print ('-'*project_max_len_chars*2)

def print_tags_data (proj_name, tags):
    fmt_str='{:<'+str(project_max_len_chars)+'} : '
    if len(tags) > 0:
        print (fmt_str.format(proj_name), end='')
        tag_i=0
        for tag in tags:
            if (tag_i>0):
                print (", ", end='')
            print (tag, end='')
            tag_i=tag_i+1
        print ("")

def print_nexus_valid_tags():
    print_tags_header ("Nexus Valid Tags", NEXUS3_PROJ_NAME_HEADER)
    for proj in projects:
        print_tags_data (proj.nexus_project_name, proj.nexus_tags.valid)
    print ("")

def print_nexus_invalid_tags():
    print_tags_header ("Nexus InValid Tags", NEXUS3_PROJ_NAME_HEADER)
    for proj in projects:
        print_tags_data (proj.nexus_project_name, proj.nexus_tags.invalid)
    print ("")

def print_docker_valid_tags():
    print_tags_header ("Docker Valid Tags", DOCKER_PROJ_NAME_HEADER)
    for proj in projects:
        print_tags_data (proj.docker_project_name, proj.docker_tags.valid)
    print ("")

def print_docker_invalid_tags():
    print_tags_header ("Docker InValid Tags", DOCKER_PROJ_NAME_HEADER)
    for proj in projects:
        print_tags_data (proj.docker_project_name, proj.docker_tags.invalid)
    print ("")

def print_stats():
    fmt_str='{:<'+str(project_max_len_chars)+'} : '
    for proj in projects:
        print ("{} : {} {} : {} {}".format(fmt_str.format(proj.docker_project_name),
            len(proj.nexus_tags.valid),
            len(proj.nexus_tags.invalid),
            len(proj.docker_tags.valid),
            len(proj.docker_tags.invalid)))
    print ("")

def print_missing_docker_proj():
    print ("Missing corresponding Docker Project")
    fmt_str='{:<'+str(project_max_len_chars)+'} : '
    print (fmt_str.format(NEXUS3_PROJ_NAME_HEADER), end='')
    print (DOCKER_PROJ_NAME_HEADER)
    print ('-'*project_max_len_chars*2)
    for proj in projects:
        if not proj.docker_tags.repository_exist:
            print (fmt_str.format(proj.nexus_project_name), end='')
            print (proj.docker_project_name)
    print("")

def print_nexus_proj_2_copy():
    print ("Nexus project to copy to docker")
    fmt_str='{:<'+str(project_max_len_chars)+'} : '
    print (fmt_str.format(NEXUS3_PROJ_NAME_HEADER), end='')
    print (DOCKER_PROJ_NAME_HEADER)
    print ('-'*project_max_len_chars*2)
    for proj in projects:
        if len(proj.tags_2_copy.valid)>0:
            print (fmt_str.format(proj.nexus_project_name), end='')
            print (proj.docker_project_name)
    print("")

def print_nexus_tags_2_copy():
    print ("Nexus project tags to copy to docker")
    fmt_str='{:<'+str(project_max_len_chars)+'} : '
    print (fmt_str.format(NEXUS3_PROJ_NAME_HEADER), end='')
    print ("Tags to copy")
    print ('-'*project_max_len_chars*2)
    for proj in projects:
        if len(proj.tags_2_copy.valid)>0:
            tag_i=0
            print (fmt_str.format(proj.nexus_project_name), end='')
            for tag in proj.tags_2_copy.valid:
                if (tag_i>0):
                    print (", ", end='')
                print (tag, end='')
                tag_i=tag_i+1
            print ("")
    print("")

def fetch_data_for_project(proj):
    new_proj = ProjectClass (proj)
    projects.append(new_proj)
    pbar.update(1)

#####
##### MAIN
#####

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Copy images from Nexus to Docker repository.')
    parser.add_argument('--repository', '-r', default="onap", type=str,
                        help='Main repository, for instance --> onap')
    parser.add_argument('--part', '-p', type=str, default="",
                        help='Only select projects that contain this string')
    parser.add_argument('--verbose', '-v', action='store_true', default=False,
                        help='Print debug statements during execution')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--copy', '-c', action='store_true', default=False,
                        help='Excecute copy of missing docker images from nexus')
    group.add_argument('--nocopy', '-n', action='store_false', default=True,
                        help='Printout mode only')

    args = parser.parse_args()

    MAIN_PART=args.repository
    FindProject=args.part
    ExecuteCopy=args.copy
    if args.verbose:
        TRACE_LEVEL=logging.DEBUG

    # Logger Levels
    # CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
    logging.basicConfig(level=TRACE_LEVEL)
    logger = logging.getLogger(__name__)


    if len(FindProject) > 0:
        logger.info("Collecting information from Nexus with projects starting with \"%s\", and containing \"%s\"" % (MAIN_PART, FindProject))
    else:
        logger.info("Collecting information from Nexus with projects starting with \"%s\"" % (MAIN_PART))
    get_nexus3_catalog()

    NbrProjects=len(NexusCatalog)
    cnt=0
    logger.info("Fetching tags from Nexus and Docker for %d projects" % NbrProjects)

    pbar = tqdm(total=len(NexusCatalog))
    pool = ThreadPool(multiprocessing.cpu_count())
    pool.map(fetch_data_for_project, NexusCatalog)
    pool.close()
    pool.join()
    pbar.close()
    print("")

    projects.sort()


    #print_nexus_docker_proj_names()
    #print_nexus_valid_tags()
    #print_nexus_invalid_tags()
    #print_docker_valid_tags()
    #print_docker_invalid_tags()
    #print_nexus_proj_2_copy()
    print_missing_docker_proj()
    print_nexus_tags_2_copy()
    #print_stats()
    #
    if ExecuteCopy:
        # Missing docker repos is created on the fly apparently.
        #create_missing_docker_projects()
        copy_from_nexus_to_docker()
