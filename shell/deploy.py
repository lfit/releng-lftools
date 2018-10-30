from io import BytesIO
from xml.etree import ElementTree as ET
import requests

class NexusRepo:

    def nexus_close_repo(self,nexus_url,staging_profile_id,staging_repo_id):
        print("functoin")
        tree = ET.fromstring("""
        <promoteRequest>
          <data>
            <stagedRepositoryId>$staging_repo_id</stagedRepositoryId>
            <description>Close staging repository.</description>
          </data>
        </promoteRequest>
        """)
        et = ET.ElementTree(tree)
        f = BytesIO()
        et.write(f, encoding='utf-8', xml_declaration=True)
        print(f.getvalue())  # your XML file, encoded as UTF-8

        request = requests.post('nexus_url/service/local/staging/profiles/${staging_profile_id}/finish',data=f.getvalue(),headers='Content-Type:application/xml')

        print(request.status_code)
        if request.status_code == "200":
            print("Repository closed")
        else:
            print("Failed to close repository")


    def nexus_create_repo(self,nexus_url,staging_profile_id,staging_repo_id):
        print("functoin")
        tree = ET.fromstring("""
        <promoteRequest>
          <data>
            <description>Create staging repo.</description>
          </data>
        </promoteRequest>
        """)
        et = ET.ElementTree(tree)
        f = BytesIO()
        et.write(f, encoding='utf-8', xml_declaration=True)
        print(f.getvalue())  # your XML file, encoded as UTF-8

        request = requests.post('nexus_url/service/local/staging/profiles/${staging_profile_id}/start',data=f.getvalue(),headers='Content-Type:application/xml')

        print(request.status_code)
        if request.status_code == "200":
            print("Repository created")
        else:
            print("Failed to create repository")

