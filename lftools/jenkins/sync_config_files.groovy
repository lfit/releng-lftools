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
import hudson.util.ReflectionUtils;
import java.lang.reflect.Field;
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

// Global variables
def projects = ["project-one" , "project-two" , "project-three"]
def servers = ["ecomp-releases", "ecomp-staging", "ecomp-site"]
GlobalConfigFiles globalConfigFiles = new GlobalConfigFiles();
ConfigFileStore storing = GlobalConfigFiles.get();

// ----- Function definitions -----

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

// Function to delete a server id on a config file
def removeServerId = { configFileId, serverId ->
    ConfigFileStore sto = GlobalConfigFiles.get();
    Config c = sto.getById("${configFileId}-settings");
    def string_id = c.name;
    def List<ServerCredentialMapping> map_list = c.serverCredentialMappings;
    println "These are the ServerIds for ${string_id} settings file: ${configFileId}-settings"
    //map_list.eachWithIndex { item, index ->
    //   println item.serverId;
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

// Function to create credentials
def createCredential = { project ->
    int randomPasswordLength = 64
    String charset = (('a'..'z') + ('A'..'Z') + ('0'..'9')).join()
    String randomPassword
    randomPassword = RandomStringUtils.random(randomPasswordLength, charset.toCharArray())
    boolean credExists = false
    Credentials cred
    println "creating credentials for ${project}"
    cred = (Credentials) new UsernamePasswordCredentialsImpl(CredentialsScope.GLOBAL,"${project}", "${project} Nexus deployment", "${project}", "${randomPassword}")
    SystemCredentialsProvider.getInstance().getStore().addCredentials(Domain.global(), cred)
}

// Function to map credentials to a config file
def mapConfig = { project ->
    MavenSettingsConfigProvider mavenSettingsProvider = new MavenSettingsConfigProvider();
    List<ServerCredentialMapping> mappings
    println "Mapping credentials for ${project}"
    mappings = new ArrayList<ServerCredentialMapping>();
    for (serv in servers) {
        println "Adding server ${serv} to ${project}"
        def mapping = new ServerCredentialMapping("${serv}", "${project}");
        mappings.add(mapping);
    }
    println "Adding the config file for ${project}"
    MavenSettingsConfig c2 = new MavenSettingsConfig("${project}-settings", "${project}-settings", "${project}-settings", mavenSettingsProvider.loadTemplateContent(), MavenSettingsConfig.isReplaceAllDefault, mappings);
    globalConfigFiles.save(c2);
    storing.save(c2);
}

// ----- Function calls -----

// Full loop that creates credentials and config files with servers and credentials mapped
for (proj in projects) {
    credExists=findCredentials("${proj}")
    if (credExists){
        println "Skipping ${proj}, credential exists"
    } else {
         createCredential("${proj}")
    }
    mapConfig("${proj}")
}

// Test calls to the methods
//removeServerId("new_project", "ecomp-site")
//addServerId("new_project", "onap-site")
//modifyServerId("new_project", "onap-site", "openecomp-site")
