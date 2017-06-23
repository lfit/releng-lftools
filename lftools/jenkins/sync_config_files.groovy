// @License EPL-1.0 <http://spdx.org/licenses/EPL-1.0>
// #############################################################################
// Copyright (c) 2017 The Linux Foundation and others.
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Eclipse Public License v1.0
// which accompanies this distribution, and is available at
// http://www.eclipse.org/legal/epl-v10.html
//
// #############################################################################

import hudson.*
import hudson.maven.MavenModuleSet
import hudson.model.*
import jenkins.*
import jenkins.model.*
import org.apache.commons.lang.RandomStringUtils
import com.cloudbees.plugins.credentials.impl.*
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.domains.*;
import org.jenkinsci.lib.configprovider.ConfigProvider
import org.jenkinsci.lib.configprovider.model.Config
import org.jenkinsci.plugins.configfiles.ConfigFilesManagement
import org.jenkinsci.plugins.configfiles.maven.GlobalMavenSettingsConfig.GlobalMavenSettingsConfigProvider
import org.jenkinsci.plugins.configfiles.maven.MavenSettingsConfig
import org.jenkinsci.plugins.configfiles.maven.security.ServerCredentialMapping
import org.jenkinsci.plugins.configfiles.maven.MavenSettingsConfig.MavenSettingsConfigProvider
import org.jenkinsci.plugins.configfiles.GlobalConfigFiles
import org.apache.commons.lang.RandomStringUtils
import org.jenkinsci.plugins.configfiles.ConfigFileStore
import org.jenkinsci.plugins.configfiles.ConfigFiles;
import java.lang.reflect.Field;
import hudson.util.ReflectionUtils;

GlobalConfigFiles globalConfigFiles = new GlobalConfigFiles();
ConfigFileStore storing = GlobalConfigFiles.get();

// Function to check if a credential exists or not
def findCredentials = { username ->
    def find_creds = com.cloudbees.plugins.credentials.CredentialsProvider.lookupCredentials(
            com.cloudbees.plugins.credentials.common.StandardUsernamePasswordCredentials.class,
            jenkins.model.Jenkins.instance
            )

    def c = find_creds.findResult { it.username == username ? it : null }

    if ( c ) {
        return true
    } else {
        return false
    }
}

def setField(String fieldName, String value, Config config) {
     Field field = ReflectionUtils.findField(config.getClass(), fieldName);
     field.setAccessible(true);
     ReflectionUtils.setField(field, config, value);
}

// Function to delete a server id on a config file
def removeServerId = { configFileId, serverId ->
 ConfigFileStore sto = GlobalConfigFiles.get();
 Config c = sto.getById("${configFileId}-settings");
 def string_id = c.name;
 def List<ServerCredentialMapping> map_list = c.serverCredentialMappings;
 println "These are the ServerIds for ${string_id} settings file: ${configFileId}-settings"
 //map_list.eachWithIndex { item, index ->
 //    println item.serverId;
 //}
 def indexToRemove;
 map_list.eachWithIndex { item, index ->
   if( item.serverId == serverId ) {
     println "Removing serverId " + item.serverId + " from config " + configFileId;
     indexToRemove = index;
   }
 }
 map_list.remove(indexToRemove);
 c.serverCredentialMappings = map_list;
 globalConfigFiles.save(c);
 storing.save(c);
}

// Function to add a server id on a config file
def addServerId = { configFileId, serverId ->
 List<ServerCredentialMapping> mappings
 ServerCredentialMapping mapping
 ConfigFileStore sto = GlobalConfigFiles.get();
 Config c = sto.getById("${configFileId}-settings");
 def string_id = c.name;
 def List<ServerCredentialMapping> map_list = c.serverCredentialMappings;
 println "Adding ${serverId} to ${string_id} settings file: ${configFileId}-setting"
 mappings = new ArrayList<ServerCredentialMapping>();
 mapping = new ServerCredentialMapping(serverId, configFileId);
 mappings.add(mapping);
 map_list.addAll(mappings);
 //map_list.add(serverId);
 c.serverCredentialMappings = map_list;
 globalConfigFiles.save(c);
 storing.save(c);
}

// Function to modify a server id on a config file
def modifyServerId = { configFileId, oldServerId, newServerId ->
 println "Renaming serverId " + oldServerId + " to " + newServerId + " from config " + configFileId;
 removeServerId(configFileId, oldServerId)
 addServerId(configFileId, newServerId)
}

println "Loop with credentials"
// Definitions needed for credentials
def projects = ["new_project"]
int randomPasswordLength = 64
String charset = (('a'..'z') + ('A'..'Z') + ('0'..'9')).join()
String randomPassword
boolean credExists = false
Credentials cred

// Definitions needed for the config files
def instance = Jenkins.getInstance()
MavenSettingsConfigProvider mavenSettingProvider;
ConfigFilesManagement config_2;
GlobalMavenSettingsConfigProvider globalMavenSettingsConfigProvider;
def servers = ["ecomp-releases", "ecomp-staging", "ecomp-site"]
MavenSettingsConfigProvider mavenSettingsProvider = new MavenSettingsConfigProvider();
List<ServerCredentialMapping> mappings
ServerCredentialMapping mapping
MavenSettingsConfig c1
MavenSettingsConfig c2

// Full loop that creates credentials and config files with servers and credentials mapped
for (proj in projects) {
  randomPassword = RandomStringUtils.random(randomPasswordLength, charset.toCharArray())
  credExists=findCredentials("${proj}")
  if (credExists){
    println "Skipping ${proj}, credential exists"
  } else {
    println "creating credentials for ${proj}"
    cred = (Credentials) new UsernamePasswordCredentialsImpl(CredentialsScope.GLOBAL,"${proj}", "${proj}", "${proj}", "${randomPassword}")
    println "creating credentials for ${proj}"
    SystemCredentialsProvider.getInstance().getStore().addCredentials(Domain.global(), cred)
    println "creating credentials for ${proj}"
  }
  println "Mapping credentials for ${proj}"
  mappings = new ArrayList<ServerCredentialMapping>();
  for (serv in servers) {
    println "Adding server ${serv} to ${proj}"
    mapping = new ServerCredentialMapping("${serv}", "${proj}");
    mappings.add(mapping);
  }
  println "Adding the config file for ${proj}"
  c1 = (MavenSettingsConfig) mavenSettingsProvider.newConfig();
  c2 = new MavenSettingsConfig("${proj}-settings", "${proj}-settings", "${proj}-settings", c1.content, MavenSettingsConfig.isReplaceAllDefault, mappings);
  //MavenSettingsConfigProvider.getInstance().getStore().addConfig(next, dumy);
  globalConfigFiles.save(c2);
  storing.save(c2);
}

removeServerId("new_project", "ecomp-site")
addServerId("new_project", "onap-site")
modifyServerId("new_project", "onap-site", "openecomp-site")
