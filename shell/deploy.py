from io import BytesIO
from xml.etree import ElementTree as ET
import requests

class NexusRepo:

    def upload_maven_file_to_nexus(self,nexus_url,nexus_repo_id,group_id,artifact_id,version,packaging,file,classifier):

        # This function is about uploading the maven file to nexus
        # Declaring Params
        params = ("-F r="+nexus_repo_id)
        params += ("-F g="+group_id)
        params += ("-F a="+artifact_id)
        params += ("-F v="+version)
        params += ("-F p="+packaging)

        if classifier:
            params += ("-F c="+classifier)
        params += ("-F file=@"+file)

        input_url = '{0}/service/local/artifact/maven/content'.format(nexus_url)

        input_header = {'Content-Type': 'application/xml'}

        response = requests.post(url=input_url,data=params,headers=input_header)

        if response.status_code == "200":
            print("File Uploaded")
        else:
            print("Failed to upload")


